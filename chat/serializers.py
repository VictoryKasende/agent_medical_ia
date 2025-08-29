from rest_framework import serializers
from authentication.models import CustomUser
from .models import FicheConsultation, Conversation, MessageIA


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'role', 'is_staff'
        ]
        read_only_fields = ['id', 'is_staff']


class FicheConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FicheConsultation
        fields = '__all__'
        read_only_fields = [
            'numero_dossier', 'date_consultation', 'heure_debut', 'heure_fin', 'created_at',
            'medecin_validateur', 'date_validation'
        ]


class ConversationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'nom', 'user', 'fiche', 'created_at', 'updated_at', 'titre']
        read_only_fields = ['id', 'created_at', 'updated_at', 'titre', 'user']


class MessageIASerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageIA
        fields = ['id', 'conversation', 'role', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp']
