from django.utils import timezone
from django.db import transaction
import hashlib
from django.core.cache import cache
from rest_framework import viewsets, status, permissions, mixins, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import FicheConsultation, Conversation, MessageIA
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from .serializers import (
    FicheConsultationSerializer,
    FicheConsultationDistanceSerializer,
    ConversationSerializer,
    ConversationDetailSerializer,
    MessageIASerializer,
    UserSerializer,
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


class RejectRequestSerializer(serializers.Serializer):
    commentaire = serializers.CharField()


@extend_schema_view(
    list=extend_schema(
        tags=['Consultations'],
        summary="Lister les fiches de consultation",
        description="Ajoute filtre ?status=a,b et ?is_patient_distance=true pour la vue distance.",
        parameters=[
            OpenApiParameter(name='status', description='Filtrer par un ou plusieurs statuts séparés par des virgules', required=False, type=str),
            OpenApiParameter(name='is_patient_distance', description='Si true, limite aux consultations distance (serializer léger)', required=False, type=bool),
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
        return qs

    def get_serializer_class(self):  # pragma: no cover simple switch
        if self.action == 'list' and self.request.query_params.get('is_patient_distance') == 'true':
            return FicheConsultationDistanceSerializer
        return FicheConsultationSerializer

    # ------- IA utils -------
    def _formater_fiche_en_texte(self, fiche: FicheConsultation) -> str:
        return (
            f"Patient {fiche.nom} {fiche.postnom} {fiche.prenom}, {fiche.age} ans. "
            f"Motif: {fiche.motif_consultation or 'Non renseigné'}. Histoire: {fiche.histoire_maladie or 'Non renseigné'}. "
            f"Signes vitaux: T={fiche.temperature or 'NA'}°C SpO2={fiche.spo2 or 'NA'}% TA={fiche.tension_arterielle or 'NA'} Pouls={fiche.pouls or 'NA'} FR={fiche.frequence_respiratoire or 'NA'}. "
            f"Plaintes: céphalées={bool(fiche.cephalees)} vertiges={bool(fiche.vertiges)} palpitations={bool(fiche.palpitations)} visuels={bool(fiche.troubles_visuels)} nycturie={bool(fiche.nycturie)}. "
            f"Antécédents: HTA={fiche.hypertendu} Diab={fiche.diabetique} Epilepsie={fiche.epileptique} TbComportement={fiche.trouble_comportement} Gastrite={fiche.gastritique}. "
            f"Mode vie: tabac={fiche.tabac} alcool={fiche.alcool} activité={fiche.activite_physique}. "
            f"Examen: état={fiche.etat} fièvre={fiche.febrile} bulbaire={fiche.coloration_bulbaire} palpébrale={fiche.coloration_palpebrale}. "
            f"Psy: préoccupations={fiche.preoccupations or 'NA'} attentes={fiche.attentes or 'NA'}."
        )

    def _lancer_analyse_async(self, fiche: FicheConsultation, conversation: Conversation):
        texte = self._formater_fiche_en_texte(fiche)
        MessageIA.objects.create(conversation=conversation, role='user', content=texte)
        cache_key = f"diagnostic_{hashlib.md5(texte.encode('utf-8')).hexdigest()}"

        def run_task():
            analyse_symptomes_task.delay(texte, conversation.user.id, conversation.id, cache_key)

        transaction.on_commit(run_task)

    def perform_create(self, serializer):
        fiche = serializer.save()
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
        tags=['Consultations'], summary='Envoyer template WhatsApp (placeholder)',
        responses={200: OpenApiResponse(description='Template envoyé (simulation)')}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecinOrAdmin], url_path='send-whatsapp')
    def send_whatsapp(self, request, pk=None):
        fiche = self.get_object()
        # Placeholder simple; future intégration réelle d'un service d'envoi.
        return Response({'detail': 'Template WhatsApp envoyé (simulation)', 'fiche': fiche.id})


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
