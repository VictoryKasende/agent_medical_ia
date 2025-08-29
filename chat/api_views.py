from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Conversation, MessageIA
from .serializers import ConversationSerializer, ConversationDetailSerializer, MessageIASerializer

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.select_related('fiche', 'user').all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Patients voient leurs conversations; medecin peut voir toutes (ajuster plus tard si besoin)
        if getattr(user, 'role', None) == 'patient':
            qs = qs.filter(user=user)
        return qs

    def get_serializer_class(self):
        if self.action in ['retrieve', 'messages']:
            return ConversationDetailSerializer
        return ConversationSerializer

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
