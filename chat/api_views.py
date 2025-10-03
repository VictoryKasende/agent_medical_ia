from django.utils import timezone
from django.db import transaction
import hashlib
from django.core.cache import cache
from rest_framework import viewsets, status, permissions, mixins, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import (
    FicheConsultation, Conversation, MessageIA, Appointment, 
    FicheMessage, FicheReference, LabResult, FicheAttachment,
    MedecinAvailability, MedecinException, WebhookEvent, DataExportJob
)
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.types import OpenApiTypes
from .serializers import (
    FicheConsultationSerializer,
    FicheConsultationDistanceSerializer,
    ConversationSerializer,
    ConversationDetailSerializer,
    MessageIASerializer,
    UserSerializer,
    AppointmentSerializer,
    FicheMessageSerializer,
    FicheReferenceSerializer,
    LabResultSerializer,
    FicheAttachmentSerializer,
    MedecinAvailabilitySerializer,
    MedecinExceptionSerializer,
    WebhookEventSerializer,
    DataExportJobSerializer,
    CalendarSlotSerializer,
)
from .tasks import analyse_symptomes_task
from authentication.permissions import IsMedecinOrAdmin, IsOwnerOrAdmin, IsMedecin, IsPatient
from .constants import (
    STATUS_EN_ANALYSE,
    STATUS_ANALYSE_TERMINEE,
    STATUS_VALIDE_MEDECIN,
    STATUS_REJETE_MEDECIN,
)
from authentication.models import CustomUser
from .models import Appointment, FicheMessage


class RejectRequestSerializer(serializers.Serializer):
    commentaire = serializers.CharField()


# ---- Appointments action serializers ----
class AssignRequestSerializer(serializers.Serializer):
    medecin_id = serializers.IntegerField()


class ConfirmRequestSerializer(serializers.Serializer):
    confirmed_start = serializers.DateTimeField()
    confirmed_end = serializers.DateTimeField()
    message_medecin = serializers.CharField(required=False, allow_blank=True)


class DeclineRequestSerializer(serializers.Serializer):
    message_medecin = serializers.CharField(required=False, allow_blank=True)


class CancelRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True)


@extend_schema_view(
    list=extend_schema(
        tags=['Consultations'],
        summary="Lister les fiches de consultation",
        description="Ajoute filtre ?status=a,b et ?is_patient_distance=true pour la vue distance.",
        parameters=[
            OpenApiParameter(name='status', description='Filtrer par un ou plusieurs statuts séparés par des virgules', required=False, type=OpenApiTypes.STR),
            OpenApiParameter(name='is_patient_distance', description='Si true, limite aux consultations distance (serializer léger)', required=False, type=OpenApiTypes.BOOL),
            OpenApiParameter(name='assigned_only', description='Pour les médecins: true pour ne voir que les fiches qui leur sont assignées', required=False, type=OpenApiTypes.BOOL),
        ],
    ),
    retrieve=extend_schema(tags=['Consultations']),
    create=extend_schema(tags=['Consultations'], summary='Créer une fiche de consultation'),
    update=extend_schema(tags=['Consultations']),
    partial_update=extend_schema(tags=['Consultations']),
    destroy=extend_schema(tags=['Consultations'])
)
class FicheConsultationViewSet(viewsets.ModelViewSet):
    """CRUD + actions d'analyse/validation pour les fiches de consultation.

    Fusion (Option B) : inclut aussi la vue "distance" via le paramètre
    `is_patient_distance=true` qui:
      - applique un filtre queryset (is_patient_distance=True)
      - utilise un serializer léger (`FicheConsultationDistanceSerializer`).
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = FicheConsultation.objects.all().order_by('-created_at')

    def get_queryset(self):  # pragma: no cover simple filtering
        qs = super().get_queryset()
        # Restrict by role: patient -> own fiches
        u = self.request.user
        if getattr(u, 'role', None) == 'patient' and not u.is_staff:
            qs = qs.filter(user=u)
        params = self.request.query_params
        # Filtre statut(s)
        status_param = params.get('status')
        if status_param:
            statuses = [s.strip() for s in status_param.split(',') if s.strip()]
            if statuses:
                qs = qs.filter(status__in=statuses)
        # Filtre distance
        if params.get('is_patient_distance') == 'true':
            qs = qs.filter(is_patient_distance=True)
        # Médecin: option pour voir uniquement ses fiches assignées
        if getattr(u, 'role', None) == 'medecin' and params.get('assigned_only') == 'true':
            qs = qs.filter(assigned_medecin=u)
        return qs

    def get_serializer_class(self):  # pragma: no cover simple switch
        if self.action == 'list' and self.request.query_params.get('is_patient_distance') == 'true':
            return FicheConsultationDistanceSerializer
        return FicheConsultationSerializer

    # ------- IA utils -------
    def _formater_fiche_en_texte(self, fiche: FicheConsultation) -> str:
        """Format amélioré de la fiche pour l'analyse IA avec tous les champs pertinents."""
        
        # Informations patient de base
        patient_info = (
            f"Patient: {fiche.nom} {fiche.postnom} {fiche.prenom}, {fiche.age} ans, "
            f"sexe {fiche.get_sexe_display() if fiche.sexe else 'NR'}, "
            f"état civil {fiche.get_etat_civil_display()}, occupation: {fiche.occupation or 'NR'}."
        )
        
        # Motif et histoire
        motif_histoire = (
            f"Motif de consultation: {fiche.motif_consultation or 'Non renseigné'}. "
            f"Histoire de la maladie: {fiche.histoire_maladie or 'Non renseigné'}."
        )
        
        # Nouveaux champs ajoutés
        hypotheses = ""
        if fiche.hypothese_patient_medecin:
            hypotheses += f"Hypothèse patient/médecin: {fiche.hypothese_patient_medecin}. "
        if fiche.analyses_proposees:
            hypotheses += f"Analyses proposées: {fiche.analyses_proposees}. "
        
        # Signes vitaux détaillés
        signes_vitaux = (
            f"Signes vitaux: Température={fiche.temperature or 'NR'}°C, "
            f"SpO2={fiche.spo2 or 'NR'}%, Poids={fiche.poids or 'NR'}kg, "
            f"TA={fiche.tension_arterielle or 'NR'}, Pouls={fiche.pouls or 'NR'}bpm, "
            f"FR={fiche.frequence_respiratoire or 'NR'}/min."
        )
        
        # Symptômes principaux
        symptomes = (
            f"Symptômes: Céphalées={self._bool_to_text(fiche.cephalees)}, "
            f"Vertiges={self._bool_to_text(fiche.vertiges)}, "
            f"Palpitations={self._bool_to_text(fiche.palpitations)}, "
            f"Troubles visuels={self._bool_to_text(fiche.troubles_visuels)}, "
            f"Nycturie={self._bool_to_text(fiche.nycturie)}."
        )
        
        # Antécédents médicaux
        antecedents = (
            f"Antécédents: HTA={self._bool_to_text(fiche.hypertendu)}, "
            f"Diabète={self._bool_to_text(fiche.diabetique)}, "
            f"Épilepsie={self._bool_to_text(fiche.epileptique)}, "
            f"Troubles comportement={self._bool_to_text(fiche.trouble_comportement)}, "
            f"Gastrite={self._bool_to_text(fiche.gastritique)}."
        )
        
        # Mode de vie
        mode_vie = (
            f"Mode de vie: Tabac={fiche.get_tabac_display()}, "
            f"Alcool={fiche.get_alcool_display()}, "
            f"Activité physique={fiche.get_activite_physique_display()}."
        )
        
        # Examen clinique
        examen = (
            f"Examen clinique: État général={fiche.get_etat_display()}, "
            f"Fébrile={fiche.get_febrile_display()}, "
            f"Coloration bulbaire={fiche.get_coloration_bulbaire_display()}, "
            f"Coloration palpébrale={fiche.get_coloration_palpebrale_display()}, "
            f"Téguments={fiche.get_tegument_display() if hasattr(fiche, 'tegument') else 'NR'}."
        )
        
        # Perceptions patient
        perceptions = ""
        if fiche.preoccupations or fiche.attentes or fiche.comprehension:
            perceptions = (
                f"Perceptions patient: Préoccupations={fiche.preoccupations or 'NR'}, "
                f"Attentes={fiche.attentes or 'NR'}, "
                f"Compréhension={fiche.comprehension or 'NR'}."
            )
        
        # Assemblage final
        texte_complet = f"{patient_info} {motif_histoire} {hypotheses} {signes_vitaux} {symptomes} {antecedents} {mode_vie} {examen} {perceptions}".strip()
        
        return texte_complet
    
    def _bool_to_text(self, value):
        """Convertit un booléen en texte lisible pour l'IA."""
        if value is True:
            return "Oui"
        elif value is False:
            return "Non"
        else:
            return "NR"  # Non renseigné

    def _lancer_analyse_async(self, fiche: FicheConsultation, conversation: Conversation):
        texte = self._formater_fiche_en_texte(fiche)
        MessageIA.objects.create(conversation=conversation, role='user', content=texte)
        cache_key = f"diagnostic_{hashlib.md5(texte.encode('utf-8')).hexdigest()}"

        def run_task():
            analyse_symptomes_task.delay(texte, conversation.user.id, conversation.id, cache_key)

        transaction.on_commit(run_task)

    def perform_create(self, serializer):
        # Attach owner if patient creates the fiche
        extra = {}
        if getattr(self.request.user, 'role', None) == 'patient':
            extra['user'] = self.request.user
        fiche = serializer.save(**extra)
        conversation = Conversation.objects.create(user=self.request.user, fiche=fiche)
        self._lancer_analyse_async(fiche, conversation)
        return fiche

    # ------- Actions -------
    @extend_schema(tags=['Consultations'], summary='Valider la consultation', responses={200: FicheConsultationSerializer})
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecinOrAdmin])
    def validate(self, request, pk=None):
        fiche = self.get_object()
        if fiche.status not in [STATUS_ANALYSE_TERMINEE, STATUS_EN_ANALYSE, STATUS_VALIDE_MEDECIN]:
            return Response({'detail': "Statut incompatible pour validation."}, status=status.HTTP_400_BAD_REQUEST)
        fiche.status = STATUS_VALIDE_MEDECIN
        fiche.medecin_validateur = request.user
        fiche.date_validation = timezone.now()
        fiche.save()
        return Response(self.get_serializer(fiche).data)

    @extend_schema(tags=['Consultations'], summary='Relancer analyse IA', responses={202: OpenApiResponse(description='Analyse relancée')})
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecinOrAdmin], url_path='relancer')
    def relancer_analyse(self, request, pk=None):
        fiche = self.get_object()
        fiche.status = STATUS_EN_ANALYSE
        fiche.save()
        conversation = fiche.conversations.first() or Conversation.objects.create(user=request.user, fiche=fiche)
        self._lancer_analyse_async(fiche, conversation)
        return Response({'detail': 'Analyse relancée', 'status': fiche.status}, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        tags=['Consultations'], summary='Rejeter la consultation',
        request=RejectRequestSerializer,
        responses={200: FicheConsultationSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecinOrAdmin], url_path='reject')
    def reject(self, request, pk=None):
        fiche = self.get_object()
        if fiche.status not in [STATUS_ANALYSE_TERMINEE, STATUS_EN_ANALYSE]:
            return Response({'detail': 'Statut incompatible pour rejet.'}, status=status.HTTP_400_BAD_REQUEST)
        commentaire = request.data.get('commentaire', '').strip()
        if not commentaire:
            return Response({'detail': 'Le champ commentaire est requis.'}, status=status.HTTP_400_BAD_REQUEST)
        fiche.status = STATUS_REJETE_MEDECIN
        fiche.commentaire_rejet = commentaire
        fiche.medecin_validateur = request.user
        fiche.date_validation = timezone.now()
        fiche.save()
        return Response(self.get_serializer(fiche).data)

    @extend_schema(
        tags=['Consultations'], 
        summary='Éditer le diagnostic médecin',
        request=serializers.Serializer(),
        responses={200: FicheConsultationSerializer}
    )
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated, IsMedecinOrAdmin], url_path='edit-diagnostic')
    def edit_diagnostic(self, request, pk=None):
        """Permet au médecin d'éditer et sauvegarder le diagnostic, traitement, recommandations."""
        fiche = self.get_object()
        
        # Champs éditables par le médecin
        editable_fields = {
            'diagnostic': request.data.get('diagnostic'),
            'traitement': request.data.get('traitement'),
            'examen_complementaire': request.data.get('examen_complementaire'),
            'recommandations': request.data.get('recommandations')
        }
        
        # Mise à jour uniquement des champs fournis
        updated = False
        for field, value in editable_fields.items():
            if value is not None:  # Permet la chaîne vide pour effacer
                setattr(fiche, field, value)
                updated = True
        
        if updated:
            # Si c'est la première édition par ce médecin, l'assigner
            if not fiche.medecin_validateur:
                fiche.medecin_validateur = request.user
                fiche.date_validation = timezone.now()
            
            fiche.save()
            
            return Response({
                'detail': 'Diagnostic médecin mis à jour avec succès',
                'fiche': self.get_serializer(fiche).data
            })
        else:
            return Response({
                'detail': 'Aucun champ à mettre à jour'
            }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Consultations'], 
        summary='Gérer les références bibliographiques de la fiche',
        request=FicheReferenceSerializer,
        responses={200: FicheReferenceSerializer(many=True), 201: FicheReferenceSerializer}
    )
    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticated], url_path='references')
    def fiche_references(self, request, pk=None):
        """Lister ou ajouter des références bibliographiques à la fiche."""
        fiche = self.get_object()
        
        # Vérifier les permissions
        u = request.user
        allowed = (
            (fiche.user_id == u.id) or
            (fiche.assigned_medecin_id == u.id) or
            u.is_staff or getattr(u, 'role', None) == 'medecin'
        )
        if not allowed:
            return Response({'detail': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            qs = fiche.references.order_by('-created_at')
            return Response(FicheReferenceSerializer(qs, many=True).data)
        
        # POST - Ajouter une référence
        serializer = FicheReferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Éviter les doublons
        existing = FicheReference.objects.filter(
            fiche=fiche,
            title=serializer.validated_data['title']
        ).exists()
        
        if existing:
            return Response({
                'detail': 'Cette référence existe déjà pour cette fiche'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reference = FicheReference.objects.create(
            fiche=fiche,
            **serializer.validated_data
        )
        
        return Response(
            FicheReferenceSerializer(reference).data, 
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        tags=['Consultations'], 
        summary='Envoyer notification au patient',
        request=serializers.Serializer(),
        responses={200: OpenApiResponse(description='Notification envoyée')}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecinOrAdmin], url_path='send-notification')
    def send_notification(self, request, pk=None):
        """Envoie une notification SMS ou WhatsApp au patient."""
        fiche = self.get_object()
        
        # Paramètres de la requête
        method = request.data.get('method', 'sms')  # sms ou whatsapp
        force_resend = request.data.get('force_resend', False)
        
        if method not in ['sms', 'whatsapp']:
            return Response({'detail': 'Method doit être "sms" ou "whatsapp"'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .notification_service import send_consultation_notification
            
            result = send_consultation_notification(fiche, method, force_resend)
            
            if result.success:
                return Response({
                    'detail': f'Notification {method} envoyée avec succès',
                    'message_sid': result.message_sid,
                    'status': result.status
                })
            else:
                return Response({
                    'detail': f'Erreur envoi {method}: {result.error}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ImportError:
            return Response({
                'detail': 'Service de notification non disponible. Installer Twilio: pip install twilio'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)

    @extend_schema(
        tags=['Consultations'], 
        summary='Envoyer template WhatsApp (legacy)',
        responses={200: OpenApiResponse(description='Template envoyé')}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecinOrAdmin], url_path='send-whatsapp')
    def send_whatsapp(self, request, pk=None):
        """Utilise le nouveau service de notification (compatibilité)."""
        fiche = self.get_object()
        
        try:
            from .notification_service import send_consultation_notification
            result = send_consultation_notification(fiche, 'whatsapp')
            
            if result.success:
                return Response({
                    'detail': 'Message WhatsApp envoyé avec succès', 
                    'fiche': fiche.id,
                    'message_sid': result.message_sid
                })
            else:
                return Response({
                    'detail': f'Erreur envoi WhatsApp: {result.error}',
                    'fiche': fiche.id
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ImportError:
            # Fallback pour compatibilité
            return Response({'detail': 'Template WhatsApp envoyé (simulation)', 'fiche': fiche.id})

    @extend_schema(tags=['Consultations'], summary='Assigner un médecin à la fiche', request=AssignRequestSerializer, responses={200: FicheConsultationSerializer})
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecinOrAdmin], url_path='assign-medecin')
    def assign_medecin(self, request, pk=None):
        ser = AssignRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        fiche = self.get_object()
        try:
            med = CustomUser.objects.get(id=ser.validated_data['medecin_id'], role='medecin')
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Médecin introuvable'}, status=status.HTTP_404_NOT_FOUND)
        fiche.assigned_medecin = med
        fiche.save()
        return Response(self.get_serializer(fiche).data)

    @extend_schema(
        tags=['Consultations'], summary='Lister/Ajouter des messages de fiche',
        request=FicheMessageSerializer,
        responses={200: FicheMessageSerializer(many=True), 201: FicheMessageSerializer}
    )
    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticated], url_path='messages')
    def fiche_messages(self, request, pk=None):
        fiche = self.get_object()
        u = request.user
        # Autorisations: patient propriétaire, médecin assigné, staff
        allowed = (
            (fiche.user_id == u.id) or
            (fiche.assigned_medecin_id == u.id) or
            u.is_staff or getattr(u, 'role', None) == 'medecin'
        )
        if not allowed:
            return Response({'detail': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        if request.method == 'GET':
            qs = fiche.messages.order_by('created_at')
            return Response(FicheMessageSerializer(qs, many=True).data)
        # POST
        serializer = FicheMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        msg = FicheMessage.objects.create(
            fiche=fiche,
            author=u,
            content=serializer.validated_data['content']
        )
        return Response(FicheMessageSerializer(msg).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Consultations'], 
        summary='Exporter la fiche en PDF',
        responses={200: OpenApiResponse(description='PDF généré')}
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        """Exporter la fiche de consultation en PDF."""
        fiche = self.get_object()
        
        # Vérifier les permissions
        u = request.user
        allowed = (
            (fiche.user_id == u.id) or
            (fiche.assigned_medecin_id == u.id) or
            u.is_staff or getattr(u, 'role', None) == 'medecin'
        )
        if not allowed:
            return Response({'detail': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            from django.template.loader import render_to_string
            from django.http import HttpResponse
            from weasyprint import HTML
            import tempfile
            import os
            
            # Préparer le contexte pour le template
            context = {
                'fiche': fiche,
                'lab_results': fiche.lab_results.all(),
                'attachments': fiche.attachments.all(),
                'references': fiche.references.all(),
                'messages': fiche.messages.all()
            }
            
            # Render HTML
            html_string = render_to_string('chat/fiche_pdf.html', context)
            
            # Générer PDF avec WeasyPrint
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                HTML(string=html_string).write_pdf(tmp_file)
                tmp_file.seek(0)
                
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="fiche_{fiche.numero_dossier}.pdf"'
                
                with open(tmp_file.name, 'rb') as pdf_file:
                    response.write(pdf_file.read())
                
                # Nettoyer le fichier temporaire
                os.unlink(tmp_file.name)
                
                return response
                
        except ImportError:
            # Fallback avec ReportLab si WeasyPrint n'est pas installé
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib import colors
                from io import BytesIO
                
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
                
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30)
                heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=12)
                
                story = []
                
                # En-tête
                story.append(Paragraph("🏥 CONSULTATION MÉDICALE", title_style))
                story.append(Spacer(1, 12))
                
                # Informations patient
                story.append(Paragraph("INFORMATIONS PATIENT", heading_style))
                patient_data = [
                    ['Nom:', fiche.user.get_full_name()],
                    ['Date de consultation:', fiche.date_consultation.strftime('%d/%m/%Y')],
                    ['Statut:', fiche.get_status_display()],
                    ['Motif:', fiche.motif_consultation],
                ]
                patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
                patient_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
                    ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                    ('FONTSIZE', (0,0), (-1,-1), 10),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                    ('BACKGROUND', (1,0), (1,-1), colors.beige),
                    ('GRID', (0,0), (-1,-1), 1, colors.black)
                ]))
                story.append(patient_table)
                story.append(Spacer(1, 20))
                
                # Diagnostic
                if fiche.diagnostic:
                    story.append(Paragraph("DIAGNOSTIC", heading_style))
                    story.append(Paragraph(fiche.diagnostic, styles['Normal']))
                    story.append(Spacer(1, 15))
                
                # Traitement
                if fiche.traitement:
                    story.append(Paragraph("TRAITEMENT", heading_style))
                    story.append(Paragraph(fiche.traitement, styles['Normal']))
                    story.append(Spacer(1, 15))
                
                # Résultats laboratoire
                lab_results = fiche.lab_results.all()
                if lab_results:
                    story.append(Paragraph("RÉSULTATS DE LABORATOIRE", heading_style))
                    for lab in lab_results:
                        lab_text = f"• {lab.type_analyse}: {lab.valeur} {lab.unite} (Normal: {lab.valeurs_normales})"
                        story.append(Paragraph(lab_text, styles['Normal']))
                    story.append(Spacer(1, 15))
                
                # Génération du PDF
                doc.build(story)
                pdf = buffer.getvalue()
                buffer.close()
                
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="fiche_{fiche.numero_dossier}.pdf"'
                return response
                
            except ImportError:
                return Response({
                    'detail': 'Export PDF non disponible. Installer WeasyPrint ou ReportLab'
                }, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as e:
            return Response({
                'detail': f'Erreur lors de la génération du PDF: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=['Consultations'], 
        summary='Exporter la fiche en JSON',
        responses={200: OpenApiResponse(description='JSON de la fiche complète')}
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='export/json')
    def export_json(self, request, pk=None):
        """Exporter la fiche de consultation en JSON complet."""
        fiche = self.get_object()
        
        # Vérifier les permissions
        u = request.user
        allowed = (
            (fiche.user_id == u.id) or
            (fiche.assigned_medecin_id == u.id) or
            u.is_staff or getattr(u, 'role', None) == 'medecin'
        )
        if not allowed:
            return Response({'detail': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        from django.http import HttpResponse
        import json
        
        # Sérialiser la fiche complète
        fiche_data = self.get_serializer(fiche).data
        
        # Ajouter les données liées
        fiche_data['lab_results'] = LabResultSerializer(
            fiche.lab_results.all(), many=True, context={'request': request}
        ).data
        fiche_data['attachments'] = FicheAttachmentSerializer(
            fiche.attachments.all(), many=True, context={'request': request}
        ).data
        fiche_data['references'] = FicheReferenceSerializer(
            fiche.references.all(), many=True
        ).data
        fiche_data['messages'] = FicheMessageSerializer(
            fiche.messages.all(), many=True
        ).data
        
        response = HttpResponse(
            json.dumps(fiche_data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="fiche_{fiche.numero_dossier}.json"'
        
        return response


@extend_schema_view(
    list=extend_schema(tags=['Conversations'], summary='Lister les conversations IA'),
    retrieve=extend_schema(tags=['Conversations'], summary='Récupérer une conversation (avec messages si serializer détail)'),
    create=extend_schema(tags=['Conversations'], summary='Créer une nouvelle conversation'),
    update=extend_schema(tags=['Conversations']),
    partial_update=extend_schema(tags=['Conversations']),
    destroy=extend_schema(tags=['Conversations'])
)
class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.select_related('fiche', 'user').all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  # pragma: no cover simple filtering
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'role', None) == 'patient':
            qs = qs.filter(user=user)
        return qs

    def get_serializer_class(self):
        if self.action in ['retrieve', 'messages']:
            return ConversationDetailSerializer
        return ConversationSerializer

    @extend_schema(
        tags=['Conversations'],
        summary='Lister ou ajouter des messages à la conversation',
        description='GET: liste des messages (ordre chronologique). POST: ajoute un message utilisateur.',
        request=MessageIASerializer,
        responses={200: MessageIASerializer(many=True), 201: MessageIASerializer}
    )
    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        conversation = self.get_object()
        if request.method == 'GET':
            msgs = conversation.messageia_set.order_by('timestamp')
            return Response(MessageIASerializer(msgs, many=True).data)
        content = request.data.get('content')
        if not content:
            return Response({'detail': 'content requis'}, status=status.HTTP_400_BAD_REQUEST)
        msg = MessageIA.objects.create(conversation=conversation, role='user', content=content)
        return Response(MessageIASerializer(msg).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(tags=['Conversations'], summary='Lister tous les messages IA (portée selon rôle)'),
    retrieve=extend_schema(tags=['Conversations'], summary='Récupérer un message IA')
)
class MessageIAViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = MessageIA.objects.all()
    serializer_class = MessageIASerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  # pragma: no cover simple filtering
        user = self.request.user
        if user.is_staff or getattr(user, 'role', None) == 'medecin':
            return MessageIA.objects.all()
        return MessageIA.objects.filter(conversation__user=user)


@extend_schema_view(
    list=extend_schema(tags=['Auth'], summary='Lister les utilisateurs (restreint staff/médecin)'),
    retrieve=extend_schema(tags=['Auth'], summary='Récupérer un utilisateur')
)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsMedecinOrAdmin]

    def list(self, request, *args, **kwargs):  # ensure restriction
        # staff/medecin déjà filtré par permission; on pourrait affiner plus tard
        return super().list(request, *args, **kwargs)


# Throttle scopes (si DRF throttling activé) – attaches dynamiquement
FicheConsultationViewSet.validate.throttle_scope = 'validate-consultation'
FicheConsultationViewSet.relancer_analyse.throttle_scope = 'relancer-analyse'
ConversationViewSet.messages.throttle_scope = 'conversation-messages'


@extend_schema_view(
    list=extend_schema(tags=['Rendez-vous'], summary='Lister les rendez-vous'),
    retrieve=extend_schema(tags=['Rendez-vous'], summary='Récupérer un rendez-vous'),
    create=extend_schema(tags=['Rendez-vous'], summary='Créer une demande de rendez-vous (patient)'),
    update=extend_schema(tags=['Rendez-vous']),
    partial_update=extend_schema(tags=['Rendez-vous']),
    destroy=extend_schema(tags=['Rendez-vous'])
)
class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related('patient', 'medecin', 'fiche').all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  # pragma: no cover - simple filtering
        qs = super().get_queryset()
        u = self.request.user
        if u.is_staff or getattr(u, 'role', None) == 'medecin':
            return qs
        # patient: ne voit que ses RDV
        return qs.filter(patient=u)

    def perform_create(self, serializer):  # pragma: no cover - simple default
        # Patient crée une demande, on force le champ patient
        request = self.request
        if request and request.user.is_authenticated:
            serializer.save(patient=request.user)
        else:
            serializer.save()

    @extend_schema(tags=['Rendez-vous'], summary='Assigner un médecin (staff ou médecin)', request=AssignRequestSerializer, responses={200: AppointmentSerializer})
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecinOrAdmin])
    def assign(self, request, pk=None):
        appt = self.get_object()
        medecin_id = request.data.get('medecin_id')
        if not medecin_id:
            return Response({'detail': 'medecin_id requis'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            med = CustomUser.objects.get(id=medecin_id)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Médecin introuvable'}, status=status.HTTP_404_NOT_FOUND)
        appt.medecin = med
        appt.save()
        return Response(self.get_serializer(appt).data)

    @extend_schema(tags=['Rendez-vous'], summary='Confirmer un créneau (médecin)', request=ConfirmRequestSerializer, responses={200: AppointmentSerializer})
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecin])
    def confirm(self, request, pk=None):
        appt = self.get_object()
        start = request.data.get('confirmed_start')
        end = request.data.get('confirmed_end')
        if not (start and end):
            return Response({'detail': 'confirmed_start et confirmed_end requis (ISO 8601)'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # DRF parse datetime automatiquement si format correct via serializer; ici parse naive
            from django.utils.dateparse import parse_datetime
            sdt = parse_datetime(start)
            edt = parse_datetime(end)
            if not sdt or not edt:
                raise ValueError
        except Exception:
            return Response({'detail': 'Format datetime invalide'}, status=status.HTTP_400_BAD_REQUEST)
        appt.confirmed_start = sdt
        appt.confirmed_end = edt
        appt.status = Appointment.Status.CONFIRMED
        appt.message_medecin = request.data.get('message_medecin', '')
        appt.save()
        return Response(self.get_serializer(appt).data)

    @extend_schema(tags=['Rendez-vous'], summary='Refuser un rendez-vous (médecin)', request=DeclineRequestSerializer, responses={200: AppointmentSerializer})
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecin])
    def decline(self, request, pk=None):
        appt = self.get_object()
        appt.status = Appointment.Status.DECLINED
        appt.message_medecin = request.data.get('message_medecin', '')
        appt.save()
        return Response(self.get_serializer(appt).data)

    @extend_schema(tags=['Rendez-vous'], summary='Annuler un rendez-vous (patient ou médecin)', request=CancelRequestSerializer, responses={200: AppointmentSerializer})
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        appt = self.get_object()
        u = request.user
        # Autoriser patient propriétaire ou médecin assigné ou staff
        if not (u.is_staff or appt.patient_id == u.id or appt.medecin_id == u.id):
            return Response({'detail': "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        appt.status = Appointment.Status.CANCELLED
        msg_field = 'message_medecin' if getattr(u, 'role', None) == 'medecin' else 'message_patient'
        setattr(appt, msg_field, request.data.get('message', ''))
        appt.save()
        return Response(self.get_serializer(appt).data)

    @extend_schema(tags=['Rendez-vous'], summary='Agenda du médecin', responses={200: AppointmentSerializer(many=True)})
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsMedecin], url_path='mon-agenda')
    def mon_agenda(self, request):
        """Endpoint pour voir l'agenda du médecin connecté avec filtres par date."""
        medecin = request.user
        qs = self.get_queryset().filter(medecin=medecin)
        
        # Filtres optionnels
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        
        if date_debut:
            qs = qs.filter(confirmed_start__date__gte=date_debut)
        if date_fin:
            qs = qs.filter(confirmed_start__date__lte=date_fin)
            
        return Response(self.get_serializer(qs, many=True).data)


@extend_schema_view(
    list=extend_schema(tags=['Références'], summary='Lister les références bibliographiques'),
    retrieve=extend_schema(tags=['Références'], summary='Récupérer une référence'),
    create=extend_schema(tags=['Références'], summary='Ajouter une référence à une fiche'),
    update=extend_schema(tags=['Références']),
    partial_update=extend_schema(tags=['Références']),
    destroy=extend_schema(tags=['Références'])
)
class FicheReferenceViewSet(viewsets.ModelViewSet):
    queryset = FicheReference.objects.all()
    serializer_class = FicheReferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Filtrer par fiche si spécifié
        fiche_id = self.request.query_params.get('fiche')
        if fiche_id:
            qs = qs.filter(fiche_id=fiche_id)
            
        # Permissions: patients voient leurs fiches, médecins voient tout
        if getattr(user, 'role', None) == 'patient' and not user.is_staff:
            qs = qs.filter(fiche__user=user)
            
        return qs


@extend_schema_view(
    list=extend_schema(tags=['Laboratoire'], summary='Lister les résultats de laboratoire'),
    retrieve=extend_schema(tags=['Laboratoire'], summary='Récupérer un résultat de laboratoire'),
    create=extend_schema(tags=['Laboratoire'], summary='Ajouter un résultat de laboratoire'),
    update=extend_schema(tags=['Laboratoire']),
    partial_update=extend_schema(tags=['Laboratoire']),
    destroy=extend_schema(tags=['Laboratoire'])
)
class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.all()
    serializer_class = LabResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Filtrer par fiche si spécifié
        fiche_id = self.request.query_params.get('fiche')
        if fiche_id:
            qs = qs.filter(fiche_id=fiche_id)
            
        # Permissions: patients voient leurs fiches, médecins voient tout
        if getattr(user, 'role', None) == 'patient' and not user.is_staff:
            qs = qs.filter(fiche__user=user)
            
        return qs

    def perform_create(self, serializer):
        # Auto-assign uploaded_by si c'est un patient
        extra = {}
        if hasattr(serializer.instance, 'fiche') and self.request.user:
            # Vérifier que l'utilisateur a le droit de modifier cette fiche
            fiche = serializer.validated_data.get('fiche')
            if fiche and getattr(self.request.user, 'role', None) == 'patient':
                if fiche.user != self.request.user:
                    raise serializers.ValidationError("Vous ne pouvez pas ajouter de résultats à cette fiche.")
        serializer.save(**extra)


@extend_schema_view(
    list=extend_schema(tags=['Pièces Jointes'], summary='Lister les pièces jointes'),
    retrieve=extend_schema(tags=['Pièces Jointes'], summary='Récupérer une pièce jointe'),
    create=extend_schema(tags=['Pièces Jointes'], summary='Uploader une pièce jointe'),
    update=extend_schema(tags=['Pièces Jointes']),
    partial_update=extend_schema(tags=['Pièces Jointes']),
    destroy=extend_schema(tags=['Pièces Jointes'])
)
class FicheAttachmentViewSet(viewsets.ModelViewSet):
    queryset = FicheAttachment.objects.all()
    serializer_class = FicheAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Filtrer par fiche si spécifié
        fiche_id = self.request.query_params.get('fiche')
        if fiche_id:
            qs = qs.filter(fiche_id=fiche_id)
            
        # Permissions: patients voient leurs fiches, médecins voient tout
        if getattr(user, 'role', None) == 'patient' and not user.is_staff:
            qs = qs.filter(fiche__user=user)
            
        return qs

    def perform_create(self, serializer):
        # Auto-assign uploaded_by
        serializer.save(uploaded_by=self.request.user)

    @extend_schema(tags=['Pièces Jointes'], summary='Télécharger le fichier', responses={200: OpenApiResponse(description='Fichier téléchargé')})
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """Endpoint sécurisé pour télécharger les fichiers."""
        attachment = self.get_object()
        if not attachment.file:
            return Response({'detail': 'Aucun fichier associé'}, status=status.HTTP_404_NOT_FOUND)
            
        from django.http import HttpResponse, Http404
        from django.conf import settings
        import os
        
        try:
            file_path = attachment.file.path
            if not os.path.exists(file_path):
                raise Http404("Fichier introuvable")
                
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                return response
        except Exception as e:
            return Response({'detail': f'Erreur de téléchargement: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(tags=['Disponibilités'], summary='Lister les disponibilités médecin'),
    retrieve=extend_schema(tags=['Disponibilités'], summary='Récupérer une disponibilité'),
    create=extend_schema(tags=['Disponibilités'], summary='Créer une disponibilité'),
    update=extend_schema(tags=['Disponibilités']),
    partial_update=extend_schema(tags=['Disponibilités']),
    destroy=extend_schema(tags=['Disponibilités'])
)
class MedecinAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = MedecinAvailability.objects.all()
    serializer_class = MedecinAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Médecins voient leurs disponibilités, staff voit tout
        if getattr(user, 'role', None) == 'medecin' and not user.is_staff:
            qs = qs.filter(medecin=user)
        elif getattr(user, 'role', None) == 'patient':
            # Patients peuvent voir les disponibilités actives pour prise de RDV
            qs = qs.filter(is_active=True)
            
        # Filtrage par médecin
        medecin_id = self.request.query_params.get('medecin')
        if medecin_id:
            qs = qs.filter(medecin_id=medecin_id)
            
        return qs

    def perform_create(self, serializer):
        # Auto-assign médecin si c'est un médecin qui crée
        if getattr(self.request.user, 'role', None) == 'medecin':
            serializer.save(medecin=self.request.user)
        else:
            serializer.save()

    @extend_schema(
        tags=['Disponibilités'], 
        summary='Générer le calendrier ICS',
        responses={200: OpenApiResponse(description='Fichier ICS généré')}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsMedecin], url_path='calendar-ics')
    def calendar_ics(self, request):
        """Génère un fichier ICS pour import dans les calendriers."""
        medecin = request.user
        availabilities = self.get_queryset().filter(medecin=medecin, is_active=True)
        
        try:
            from datetime import datetime, timedelta
            
            # Générer ICS basique
            ics_content = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Agent Medical IA//Disponibilites Medecin//FR",
                "CALSCALE:GREGORIAN",
                "METHOD:PUBLISH"
            ]
            
            # Générer événements pour les 12 prochaines semaines
            today = datetime.now().date()
            for week in range(12):
                week_start = today + timedelta(weeks=week)
                
                for availability in availabilities:
                    # Calculer la date de ce jour de la semaine
                    days_ahead = availability.day_of_week - week_start.weekday()
                    if days_ahead < 0:
                        days_ahead += 7
                    event_date = week_start + timedelta(days=days_ahead)
                    
                    # Créer l'événement ICS
                    start_datetime = datetime.combine(event_date, availability.start_time)
                    end_datetime = datetime.combine(event_date, availability.end_time)
                    
                    ics_content.extend([
                        "BEGIN:VEVENT",
                        f"DTSTART:{start_datetime.strftime('%Y%m%dT%H%M%S')}",
                        f"DTEND:{end_datetime.strftime('%Y%m%dT%H%M%S')}",
                        f"SUMMARY:Disponible - {availability.get_consultation_type_display()}",
                        f"DESCRIPTION:Durée: {availability.duration_formatted}",
                        f"LOCATION:{availability.location or 'Téléconsultation'}",
                        f"UID:{availability.id}-{event_date.strftime('%Y%m%d')}@agent-medical-ia.com",
                        "END:VEVENT"
                    ])
            
            ics_content.append("END:VCALENDAR")
            
            response = HttpResponse(
                '\r\n'.join(ics_content),
                content_type='text/calendar; charset=utf-8'
            )
            response['Content-Disposition'] = f'attachment; filename="disponibilites_dr_{medecin.username}.ics"'
            
            return response
            
        except Exception as e:
            return Response({
                'detail': f'Erreur génération ICS: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=['Disponibilités'], 
        summary='Créneaux disponibles pour période',
        parameters=[
            OpenApiParameter('date_start', OpenApiTypes.DATE, description='Date de début'),
            OpenApiParameter('date_end', OpenApiTypes.DATE, description='Date de fin'),
            OpenApiParameter('consultation_type', OpenApiTypes.STR, description='Type de consultation'),
        ],
        responses={200: CalendarSlotSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='available-slots')
    def available_slots(self, request):
        """Retourne les créneaux disponibles pour une période donnée."""
        from datetime import datetime, timedelta, time
        
        # Paramètres
        date_start = request.query_params.get('date_start')
        date_end = request.query_params.get('date_end')
        consultation_type = request.query_params.get('consultation_type')
        medecin_id = request.query_params.get('medecin')
        
        if not date_start or not date_end:
            return Response({
                'detail': 'Paramètres date_start et date_end requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = datetime.strptime(date_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'detail': 'Format de date invalide (YYYY-MM-DD attendu)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Limiter à 4 semaines max
        if (end_date - start_date).days > 28:
            return Response({
                'detail': 'Période maximale: 4 semaines'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Récupérer les disponibilités
        availabilities = self.get_queryset().filter(is_active=True)
        if medecin_id:
            availabilities = availabilities.filter(medecin_id=medecin_id)
        if consultation_type:
            availabilities = availabilities.filter(
                consultation_type__in=[consultation_type, 'both']
            )
        
        slots = []
        current_date = start_date
        
        while current_date <= end_date:
            day_availabilities = availabilities.filter(day_of_week=current_date.weekday())
            
            for availability in day_availabilities:
                # Vérifier exceptions
                exceptions = MedecinException.objects.filter(
                    medecin=availability.medecin,
                    start_datetime__date__lte=current_date,
                    end_datetime__date__gte=current_date
                )
                
                if exceptions.exists():
                    continue  # Médecin indisponible ce jour
                
                # Calculer les créneaux
                start_datetime = datetime.combine(current_date, availability.start_time)
                end_datetime = datetime.combine(current_date, availability.end_time)
                
                # Vérifier combien de consultations déjà prises
                booked_count = Appointment.objects.filter(
                    medecin=availability.medecin,
                    confirmed_start__date=current_date,
                    status__in=['confirmed', 'pending']
                ).count()
                
                slots.append({
                    'datetime': start_datetime,
                    'end_datetime': end_datetime,
                    'available': booked_count < availability.max_consultations,
                    'consultation_type': availability.consultation_type,
                    'location': availability.location,
                    'medecin_id': availability.medecin.id,
                    'medecin_name': availability.medecin.get_full_name() or availability.medecin.username,
                    'duration_minutes': availability.duration_minutes,
                    'max_consultations': availability.max_consultations,
                    'booked_consultations': booked_count
                })
            
            current_date += timedelta(days=1)
        
        return Response(CalendarSlotSerializer(slots, many=True).data)


@extend_schema_view(
    list=extend_schema(tags=['Disponibilités'], summary='Lister les exceptions médecin'),
    retrieve=extend_schema(tags=['Disponibilités'], summary='Récupérer une exception'),
    create=extend_schema(tags=['Disponibilités'], summary='Créer une exception'),
    update=extend_schema(tags=['Disponibilités']),
    partial_update=extend_schema(tags=['Disponibilités']),
    destroy=extend_schema(tags=['Disponibilités'])
)
class MedecinExceptionViewSet(viewsets.ModelViewSet):
    queryset = MedecinException.objects.all()
    serializer_class = MedecinExceptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsMedecinOrAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Médecins voient leurs exceptions, staff voit tout
        if getattr(user, 'role', None) == 'medecin' and not user.is_staff:
            qs = qs.filter(medecin=user)
            
        return qs

    def perform_create(self, serializer):
        # Auto-assign médecin si c'est un médecin qui crée
        if getattr(self.request.user, 'role', None) == 'medecin':
            serializer.save(medecin=self.request.user)
        else:
            serializer.save()


@extend_schema_view(
    list=extend_schema(tags=['Webhooks'], summary='Lister les événements webhook'),
    retrieve=extend_schema(tags=['Webhooks'], summary='Récupérer un événement webhook'),
    create=extend_schema(tags=['Webhooks'], summary='Traiter un webhook entrant'),
)
class WebhookEventViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, 
                         mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = WebhookEvent.objects.all()
    serializer_class = WebhookEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Seuls staff et médecins peuvent voir les webhooks
        if not (user.is_staff or getattr(user, 'role', None) == 'medecin'):
            return qs.none()
            
        # Filtres
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(processing_status=status_filter)
            
        event_type = self.request.query_params.get('event_type')
        if event_type:
            qs = qs.filter(event_type=event_type)
            
        return qs

    def perform_create(self, serializer):
        """Traite un webhook entrant et tente de l'associer automatiquement."""
        webhook = serializer.save()
        
        try:
            # Tenter de trouver l'utilisateur par numéro
            user = None
            try:
                # Normaliser le numéro (enlever espaces, +, etc.)
                clean_phone = ''.join(filter(str.isdigit, webhook.sender_phone))
                if len(clean_phone) >= 9:  # Au moins 9 chiffres
                    # Chercher par fin de numéro (les 9 derniers chiffres)
                    from django.db.models import Q
                    phone_query = Q(telephone__icontains=clean_phone[-9:])
                    
                    # Essayer aussi avec +33, 0033, etc. pour la France
                    if clean_phone.startswith('33') and len(clean_phone) >= 10:
                        national_number = '0' + clean_phone[2:]
                        phone_query |= Q(telephone__icontains=national_number[-9:])
                    
                    user = CustomUser.objects.filter(phone_query).first()
                    
            except Exception as e:
                webhook.processing_error = f"Erreur recherche utilisateur: {e}"
            
            if user:
                webhook.related_user = user
                
                # Tenter de trouver une fiche récente
                recent_fiche = FicheConsultation.objects.filter(
                    user=user
                ).order_by('-created_at').first()
                
                if recent_fiche:
                    webhook.related_fiche = recent_fiche
                    
                    # Créer un message dans la fiche
                    message = FicheMessage.objects.create(
                        fiche=recent_fiche,
                        author=user,
                        content=webhook.content
                    )
                    webhook.created_message = message
                
                webhook.mark_processed(message if 'message' in locals() else None)
            else:
                webhook.processing_status = WebhookEvent.ProcessingStatus.IGNORED
                webhook.processing_error = "Utilisateur non trouvé"
                webhook.save()
                
        except Exception as e:
            webhook.mark_failed(e)

    @extend_schema(
        tags=['Webhooks'], 
        summary='Endpoint Twilio WhatsApp',
        request=None,
        responses={200: OpenApiResponse(description='Webhook traité')}
    )
    @action(detail=False, methods=['post'], permission_classes=[], url_path='twilio/whatsapp')
    def twilio_whatsapp(self, request):
        """Endpoint pour webhooks Twilio WhatsApp entrants."""
        try:
            # Valider la signature Twilio (sécurité)
            # Note: Implémentation simplifiée, ajouter validation signature en production
            
            data = request.data if hasattr(request, 'data') else request.POST
            
            webhook_data = {
                'event_type': 'whatsapp_incoming',
                'external_id': data.get('MessageSid', ''),
                'sender_phone': data.get('From', '').replace('whatsapp:', ''),
                'recipient_phone': data.get('To', '').replace('whatsapp:', ''),
                'content': data.get('Body', ''),
                'raw_payload': dict(data)
            }
            
            # Créer l'événement webhook
            serializer = self.get_serializer(data=webhook_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({'status': 'received'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=['Webhooks'], 
        summary='Endpoint Twilio SMS',
        request=None,
        responses={200: OpenApiResponse(description='Webhook traité')}
    )
    @action(detail=False, methods=['post'], permission_classes=[], url_path='twilio/sms')
    def twilio_sms(self, request):
        """Endpoint pour webhooks Twilio SMS entrants."""
        try:
            data = request.data if hasattr(request, 'data') else request.POST
            
            webhook_data = {
                'event_type': 'sms_incoming',
                'external_id': data.get('MessageSid', ''),
                'sender_phone': data.get('From', ''),
                'recipient_phone': data.get('To', ''),
                'content': data.get('Body', ''),
                'raw_payload': dict(data)
            }
            
            # Créer l'événement webhook
            serializer = self.get_serializer(data=webhook_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({'status': 'received'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(tags=['Exports'], summary='Lister les jobs d\'export'),
    retrieve=extend_schema(tags=['Exports'], summary='Récupérer un job d\'export'),
    create=extend_schema(tags=['Exports'], summary='Créer un export de données'),
)
class DataExportJobViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, 
                          mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = DataExportJob.objects.all()
    serializer_class = DataExportJobSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Seuls les admins peuvent voir tous les exports
        if not user.is_staff:
            qs = qs.filter(created_by=user)
            
        return qs

    def perform_create(self, serializer):
        """Lance un job d'export de données."""
        export_job = serializer.save(created_by=self.request.user)
        
        # Lancer le traitement en arrière-plan (Celery)
        from .tasks import process_data_export
        process_data_export.delay(export_job.id)

    @extend_schema(
        tags=['Exports'], 
        summary='Télécharger le fichier d\'export',
        responses={200: OpenApiResponse(description='Fichier téléchargé')}
    )
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """Télécharge le fichier d'export généré."""
        export_job = self.get_object()
        
        if export_job.status != DataExportJob.ExportStatus.COMPLETED:
            return Response({
                'detail': 'Export pas encore terminé'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not export_job.file_path:
            return Response({
                'detail': 'Fichier non disponible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            import os
            if not os.path.exists(export_job.file_path):
                return Response({
                    'detail': 'Fichier introuvable sur le serveur'
                }, status=status.HTTP_404_NOT_FOUND)
            
            with open(export_job.file_path, 'rb') as f:
                content_type = 'application/octet-stream'
                if export_job.export_format == 'csv':
                    content_type = 'text/csv'
                elif export_job.export_format == 'json':
                    content_type = 'application/json'
                elif export_job.export_format == 'excel':
                    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                
                response = HttpResponse(f.read(), content_type=content_type)
                filename = os.path.basename(export_job.file_path)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                return response
                
        except Exception as e:
            return Response({
                'detail': f'Erreur téléchargement: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

