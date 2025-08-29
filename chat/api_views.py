from django.utils import timezone
from django.db import transaction
import hashlib
from django.core.cache import cache

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import FicheConsultation, Conversation, MessageIA
from .serializers import (
    FicheConsultationSerializer,
    ConversationSerializer,
    ConversationDetailSerializer,
    MessageIASerializer,
)
from .tasks import analyse_symptomes_task


class IsMedecin(permissions.BasePermission):
    """Permission: uniquement les utilisateurs role == 'medecin'."""

    def has_permission(self, request, view):  # pragma: no cover simple check
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

    def get_queryset(self):  # pragma: no cover simple filtering
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            statuses = [s.strip() for s in status_param.split(',') if s.strip()]
            if statuses:
                qs = qs.filter(status__in=statuses)
        return qs

    # -------- Utilitaires internes (analyse IA) --------
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
        # Création fiche + conversation initiale + déclenchement analyse
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
    MessageIASerializer,
    UserSerializer,
)
from authentication.models import CustomUser
from authentication.permissions import (
    IsMedecin, IsPatient, IsAdmin, IsOwnerOrAdmin, IsMedecinOrAdmin
)


class FicheConsultationViewSet(viewsets.ModelViewSet):
    queryset = FicheConsultation.objects.all()
    serializer_class = FicheConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Patients only see their own? We have no FK to user; assume open list for medecin/admin.
        user = self.request.user
        if user.is_staff or user.role == 'medecin':
            return FicheConsultation.objects.all()
        # For patient role, could restrict later if linkage exists. Return latest limited subset.
        return FicheConsultation.objects.order_by('-created_at')[:50]

    def get_permissions(self):
        if self.action in ['validate_consultation']:
            return [IsMedecinOrAdmin()]
        if self.action in ['relancer_analyse']:
            return [IsMedecinOrAdmin()]
        return super().get_permissions()

    @action(detail=True, methods=['post'], url_path='validate')
    def validate_consultation(self, request, pk=None):
        fiche = self.get_object()
        if fiche.status not in ['analyse_terminee', 'en_analyse']:
            return Response({'detail': 'Statut incompatible pour validation.'}, status=400)
        fiche.status = 'valide_medecin'
        fiche.medecin_validateur = request.user
        fiche.date_validation = timezone.now()
        fiche.save()
        return Response(FicheConsultationSerializer(fiche, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsMedecin], url_path='relancer-analyse')
        return Response(self.get_serializer(fiche).data)

    @action(detail=True, methods=['post'], url_path='relancer')
    def relancer_analyse(self, request, pk=None):
        fiche = self.get_object()
        fiche.status = 'en_analyse'
        fiche.save()
        conversation = fiche.conversations.first()
        if not conversation:
            conversation = Conversation.objects.create(user=request.user, fiche=fiche)
        self._lancer_analyse_async(fiche, conversation)
        return Response({'detail': 'Analyse relancée', 'status': fiche.status}, status=status.HTTP_202_ACCEPTED)

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):  # pragma: no cover simple rule
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, 'user', None) == request.user


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.select_related('fiche', 'user').all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):  # pragma: no cover (simple filtering logic)
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, 'role', None) == 'patient':
            qs = qs.filter(user=user)
        return qs

    def get_serializer_class(self):
        if self.action in ['retrieve', 'messages']:
            return ConversationDetailSerializer
        return ConversationSerializer
        return Response({'detail': 'Analyse relancée', 'status': fiche.status})


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'medecin':
            return Conversation.objects.all()
        return Conversation.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        conversation = self.get_object()
        if request.method == 'GET':
            msgs = conversation.messageia_set.order_by('timestamp')
            return Response(MessageIASerializer(msgs, many=True).data)
        # POST => créer un message utilisateur
        role = request.data.get('role', 'user')
        content = request.data.get('content')
        if not content:
            return Response({'detail': 'content requis'}, status=status.HTTP_400_BAD_REQUEST)
        msg = MessageIA.objects.create(conversation=conversation, role=role, content=content)
        return Response(MessageIASerializer(msg).data, status=status.HTTP_201_CREATED)
        conv = self.get_object()
        if request.method == 'GET':
            qs = MessageIA.objects.filter(conversation=conv).order_by('timestamp')
            return Response(MessageIASerializer(qs, many=True).data)
        content = request.data.get('content')
        if not content:
            return Response({'detail': 'content requis'}, status=400)
        msg = MessageIA.objects.create(conversation=conv, role='user', content=content)
        return Response(MessageIASerializer(msg).data, status=201)

# Assign throttle scopes to actions (cannot be passed as decorator kwargs because they become initkwargs)
FicheConsultationViewSet.validate_consultation.throttle_scope = 'validate-consultation'
FicheConsultationViewSet.relancer_analyse.throttle_scope = 'relancer-analyse'
ConversationViewSet.messages.throttle_scope = 'conversation-messages'


class MessageIAViewSet(mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    queryset = MessageIA.objects.all()
    serializer_class = MessageIASerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'medecin':
            return MessageIA.objects.all()
        return MessageIA.objects.filter(conversation__user=user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list']:
            return [IsAdmin()]
        return super().get_permissions()
