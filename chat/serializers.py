from rest_framework import serializers
from authentication.models import CustomUser
from .models import FicheConsultation, Conversation, MessageIA, Appointment
from drf_spectacular.utils import extend_schema_field


class FicheConsultationSerializer(serializers.ModelSerializer):
    """Serializer principal unifié pour FicheConsultation (version API refonte).

    - Expose tous les champs (create/update) sauf ceux générés serveur.
    - `status` est en lecture seule; transitions via actions custom du ViewSet.
    - Ajoute `status_display` pour éviter logique côté client.
    """

    status_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FicheConsultation
        fields = '__all__'
        read_only_fields = [
            'id', 'numero_dossier', 'date_consultation', 'heure_debut', 'heure_fin', 'created_at',
            'status', 'status_display', 'diagnostic_ia', 'medecin_validateur', 'date_validation', 'signature_medecin'
        ]

    @extend_schema_field(serializers.CharField())
    def get_status_display(self, obj):  # pragma: no cover - simple mapping
        return obj.get_status_display()


class FicheConsultationDistanceSerializer(serializers.ModelSerializer):
    """Serializer léger pour les consultations distance (liste/lecture).

    Utilisé quand le paramètre de requête `is_patient_distance=true` est fourni
    sur l'endpoint principal `fiche-consultation`. Fournit un sous-ensemble
    des champs pertinents pour la vue remote + un bool dérivé.
    """

    status_display = serializers.SerializerMethodField(read_only=True)
    febrile_bool = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FicheConsultation
        fields = [
            'id', 'nom', 'prenom', 'age', 'telephone',
            'created_at', 'status', 'status_display',
            'motif_consultation', 'histoire_maladie', 'cephalees', 'febrile', 'febrile_bool',
            'temperature', 'tension_arterielle', 'pouls', 'spo2',
            'diagnostic_ia'
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField())
    def get_status_display(self, obj):  # pragma: no cover simple mapping
        return obj.get_status_display()

    @extend_schema_field(serializers.BooleanField())
    def get_febrile_bool(self, obj):  # pragma: no cover simple mapping
        return True if getattr(obj, 'febrile', None) == 'Oui' else False


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'role', 'is_staff'
        ]
        read_only_fields = ['id', 'is_staff']


class MessageIASerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageIA
        fields = ['id', 'conversation', 'role', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp', 'conversation']


class ConversationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    # Utiliser SerializerMethodField car source 'messageia_set.count' ne déclenche pas la fonction d'agrégation souhaitée.
    messages_count = serializers.SerializerMethodField()
    first_message = serializers.SerializerMethodField()
    titre = serializers.CharField(read_only=True)
    fiche_numero = serializers.CharField(source='fiche.numero_dossier', read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id', 'nom', 'titre', 'user', 'fiche', 'fiche_numero',
            'created_at', 'updated_at', 'messages_count', 'first_message'
        ]
        read_only_fields = [
            'id', 'titre', 'user', 'created_at', 'updated_at', 'messages_count', 'first_message', 'fiche_numero'
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_first_message(self, obj):  # pragma: no cover - simple mapping
        msg = obj.messageia_set.order_by('timestamp').first()
        return msg.content if msg else None

    @extend_schema_field(serializers.IntegerField())
    def get_messages_count(self, obj):  # pragma: no cover - simple mapping
        return obj.messageia_set.count()

    def create(self, validated_data):  # pragma: no cover - simple override
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageIASerializer(source='messageia_set', many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']
        read_only_fields = ConversationSerializer.Meta.read_only_fields + ['messages']


class AppointmentSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField(read_only=True)
    patient_username = serializers.CharField(source='patient.username', read_only=True)
    medecin_username = serializers.CharField(source='medecin.username', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_username', 'medecin', 'medecin_username', 'fiche',
            'requested_start', 'requested_end', 'confirmed_start', 'confirmed_end',
            'status', 'status_display', 'message_patient', 'message_medecin',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status_display', 'created_at', 'updated_at', 'confirmed_start', 'confirmed_end']

    @extend_schema_field(serializers.CharField())
    def get_status_display(self, obj):
        return obj.get_status_display()

    def validate(self, attrs):
        req_start = attrs.get('requested_start')
        req_end = attrs.get('requested_end')
        if req_start and req_end and req_end <= req_start:
            raise serializers.ValidationError({'requested_end': "Doit être postérieur à requested_start."})
        return attrs
