from django.utils import timezone
from django.db import transaction
import hashlib
from django.core.cache import cache

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import FicheConsultation, Conversation, MessageIA
from .serializers import FicheConsultationSerializer
from .tasks import analyse_symptomes_task


class IsMedecin(permissions.BasePermission):
    """Permission: uniquement les utilisateurs role == 'medecin'."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'medecin')


class FicheConsultationViewSet(viewsets.ModelViewSet):
    """API REST CRUD pour les fiches de consultation.

    Actions supplémentaires:
    - validate (POST): validation par un médecin -> status = valide_medecin
    - relancer_analyse (POST): relance l'analyse IA -> status = en_analyse
    """

    serializer_class = FicheConsultationSerializer
    queryset = FicheConsultation.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # TODO: si un champ auteur est ajouté plus tard, filtrer ici pour patients.
        if getattr(user, 'role', None) == 'patient':
            # Pour l'instant pas de restriction faute de lien User -> Fiche.
            return qs
        return qs

    # -------- Utilitaires internes --------
    def _formater_fiche_en_texte(self, fiche: FicheConsultation) -> str:
        """Version condensée du formatage texte pour l'analyse IA."""
        texte = (
            f"Patient {fiche.nom} {fiche.postnom} {fiche.prenom}, {fiche.age} ans. "
            f"Motif: {fiche.motif_consultation or 'Non renseigné'}. Histoire: {fiche.histoire_maladie or 'Non renseigné'}. "
            f"Signes vitaux: T={fiche.temperature or 'NA'}°C SpO2={fiche.spo2 or 'NA'}% TA={fiche.tension_arterielle or 'NA'} Pouls={fiche.pouls or 'NA'} FR={fiche.frequence_respiratoire or 'NA'}. "
            f"Plaintes: céphalées={bool(fiche.cephalees)} vertiges={bool(fiche.vertiges)} palpitations={bool(fiche.palpitations)} visuels={bool(fiche.troubles_visuels)} nycturie={bool(fiche.nycturie)}. "
            f"Antécédents: HTA={fiche.hypertendu} Diab={fiche.diabetique} Epilepsie={fiche.epileptique} TbComportement={fiche.trouble_comportement} Gastrite={fiche.gastritique}. "
            f"Mode vie: tabac={fiche.tabac} alcool={fiche.alcool} activité={fiche.activite_physique}. "
            f"Examen: état={fiche.etat} fièvre={fiche.febrile} bulbaire={fiche.coloration_bulbaire} palpébrale={fiche.coloration_palpebrale}. "
            f"Psy: préoccupations={fiche.preoccupations or 'NA'} attentes={fiche.attentes or 'NA'}."
        )
        return texte

    def _lancer_analyse_async(self, fiche: FicheConsultation, conversation: Conversation):
        texte = self._formater_fiche_en_texte(fiche)
        MessageIA.objects.create(conversation=conversation, role='user', content=texte)
        hash_key = hashlib.md5(texte.encode('utf-8')).hexdigest()
        cache_key = f"diagnostic_{hash_key}"

        def run_task():
            analyse_symptomes_task.delay(texte, conversation.user.id, conversation.id, cache_key)

        transaction.on_commit(run_task)

    def perform_create(self, serializer):
        fiche = serializer.save()  # status initial via modèle
        conversation = Conversation.objects.create(user=self.request.user, fiche=fiche)
        self._lancer_analyse_async(fiche, conversation)
        return fiche

    # -------- Actions personnalisées --------
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecin])
    def validate(self, request, pk=None):
        fiche = self.get_object()
        if fiche.status not in ['analyse_terminee', 'valide_medecin']:
            return Response({'detail': "La fiche doit être 'analyse_terminee' avant validation."}, status=status.HTTP_400_BAD_REQUEST)
        fiche.status = 'valide_medecin'
        fiche.medecin_validateur = request.user
        fiche.date_validation = timezone.now()
        fiche.save()
        return Response(FicheConsultationSerializer(fiche, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecin], url_path='relancer-analyse')
    def relancer_analyse(self, request, pk=None):
        fiche = self.get_object()
        fiche.status = 'en_analyse'
        fiche.save()
        conversation = fiche.conversations.first()
        if not conversation:
            conversation = Conversation.objects.create(user=request.user, fiche=fiche)
        self._lancer_analyse_async(fiche, conversation)
        return Response({'detail': 'Analyse relancée', 'status': fiche.status}, status=status.HTTP_202_ACCEPTED)
