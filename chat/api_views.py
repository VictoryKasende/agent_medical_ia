from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import FicheConsultation, Conversation, MessageIA
from .serializers import (
    FicheConsultationSerializer,
    ConversationSerializer,
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
        return Response(self.get_serializer(fiche).data)

    @action(detail=True, methods=['post'], url_path='relancer')
    def relancer_analyse(self, request, pk=None):
        fiche = self.get_object()
        fiche.status = 'en_analyse'
        fiche.save()
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
