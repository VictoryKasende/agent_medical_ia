from rest_framework import serializers
from .models import Conversation, MessageIA, FicheConsultation

class MessageIASerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageIA
        fields = ['id', 'conversation', 'role', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp', 'conversation']

class ConversationSerializer(serializers.ModelSerializer):
    messages_count = serializers.IntegerField(source='messageia_set.count', read_only=True)
    first_message = serializers.SerializerMethodField()
    fiche_numero = serializers.CharField(source='fiche.numero_dossier', read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'nom', 'titre', 'user', 'fiche', 'fiche_numero', 'created_at', 'updated_at', 'messages_count', 'first_message']
        read_only_fields = ['id', 'titre', 'user', 'created_at', 'updated_at', 'messages_count', 'first_message', 'fiche_numero']

    def get_first_message(self, obj):
        msg = obj.messageia_set.order_by('timestamp').first()
        return msg.content if msg else None

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)

class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageIASerializer(source='messageia_set', many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']
        read_only_fields = ConversationSerializer.Meta.read_only_fields + ['messages']
