from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from authentication.models import CustomUser

from .models import (
    Appointment,
    Conversation,
    DataExportJob,
    FicheAttachment,
    FicheConsultation,
    FicheMessage,
    FicheReference,
    LabResult,
    MedecinAvailability,
    MedecinException,
    MessageIA,
    WebhookEvent,
)


class FicheConsultationSerializer(serializers.ModelSerializer):
    """Serializer principal unifié pour FicheConsultation (version API refonte).

    - Expose tous les champs (create/update) sauf ceux générés serveur.
    - `status` est en lecture seule; transitions via actions custom du ViewSet.
    - Ajoute `status_display` pour éviter logique côté client.
    """

    status_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FicheConsultation
        fields = "__all__"
        read_only_fields = [
            "id",
            "numero_dossier",
            "date_consultation",
            "heure_debut",
            "heure_fin",
            "created_at",
            "status",
            "status_display",
            "diagnostic_ia",
            "medecin_validateur",
            "date_validation",
            #"signature_medecin",
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
            "id",
            "nom",
            "prenom",
            "age",
            "telephone",
            "created_at",
            "status",
            "status_display",
            "motif_consultation",
            "histoire_maladie",
            "cephalees",
            "febrile",
            "febrile_bool",
            "temperature",
            "tension_arterielle",
            "pouls",
            "spo2",
            "diagnostic_ia",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.CharField())
    def get_status_display(self, obj):  # pragma: no cover simple mapping
        return obj.get_status_display()

    @extend_schema_field(serializers.BooleanField())
    def get_febrile_bool(self, obj):  # pragma: no cover simple mapping
        return True if getattr(obj, "febrile", None) == "Oui" else False


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "username", "first_name", "last_name", "email", "role", "is_staff"]
        read_only_fields = ["id", "is_staff"]


class MessageIASerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageIA
        fields = ["id", "conversation", "role", "content", "timestamp"]
        read_only_fields = ["id", "timestamp", "conversation"]


class ConversationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    # Utiliser SerializerMethodField car source 'messageia_set.count' ne déclenche pas la fonction d'agrégation souhaitée.
    messages_count = serializers.SerializerMethodField()
    first_message = serializers.SerializerMethodField()
    titre = serializers.CharField(read_only=True)
    fiche_numero = serializers.CharField(source="fiche.numero_dossier", read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "nom",
            "titre",
            "user",
            "fiche",
            "fiche_numero",
            "created_at",
            "updated_at",
            "messages_count",
            "first_message",
        ]
        read_only_fields = [
            "id",
            "titre",
            "user",
            "created_at",
            "updated_at",
            "messages_count",
            "first_message",
            "fiche_numero",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_first_message(self, obj):  # pragma: no cover - simple mapping
        msg = obj.messageia_set.order_by("timestamp").first()
        return msg.content if msg else None

    @extend_schema_field(serializers.IntegerField())
    def get_messages_count(self, obj):  # pragma: no cover - simple mapping
        return obj.messageia_set.count()

    def create(self, validated_data):  # pragma: no cover - simple override
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["user"] = request.user
        return super().create(validated_data)


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageIASerializer(source="messageia_set", many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ["messages"]
        read_only_fields = ConversationSerializer.Meta.read_only_fields + ["messages"]


class FicheMessageSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = FicheMessage
        fields = ["id", "fiche", "author", "author_username", "content", "created_at"]
        read_only_fields = ["id", "author", "author_username", "created_at"]


class AppointmentSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField(read_only=True)
    consultation_mode_display = serializers.SerializerMethodField(read_only=True)
    patient_username = serializers.CharField(source="patient.username", read_only=True)
    medecin_username = serializers.CharField(source="medecin.username", read_only=True)
    # Le champ patient est optionnel pour la création (sera auto-rempli par perform_create)
    patient = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_username",
            "medecin",
            "medecin_username",
            "fiche",
            "requested_start",
            "requested_end",
            "confirmed_start",
            "confirmed_end",
            "consultation_mode",
            "consultation_mode_display",
            "location_note",
            "status",
            "status_display",
            "message_patient",
            "message_medecin",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status_display",
            "consultation_mode_display",
            "created_at",
            "updated_at",
            "confirmed_start",
            "confirmed_end",
        ]

    @extend_schema_field(serializers.CharField())
    def get_status_display(self, obj):
        return obj.get_status_display()

    @extend_schema_field(serializers.CharField())
    def get_consultation_mode_display(self, obj):
        return obj.get_consultation_mode_display()

    def validate(self, attrs):
        req_start = attrs.get("requested_start")
        req_end = attrs.get("requested_end")
        if req_start and req_end and req_end <= req_start:
            raise serializers.ValidationError({"requested_end": "Doit être postérieur à requested_start."})
        return attrs


class FicheReferenceSerializer(serializers.ModelSerializer):
    source_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FicheReference
        fields = ["id", "fiche", "title", "url", "source", "source_display", "authors", "year", "journal", "created_at"]
        read_only_fields = ["id", "created_at", "source_display"]

    @extend_schema_field(serializers.CharField())
    def get_source_display(self, obj):
        return obj.get_source_display()


class LabResultSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LabResult
        fields = [
            "id",
            "fiche",
            "type_analyse",
            "valeur",
            "unite",
            "valeurs_normales",
            "date_prelevement",
            "laboratoire",
            "fichier",
            "file_url",
            "commentaire",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "file_url"]

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_file_url(self, obj):
        if obj.fichier:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.fichier.url)
            return obj.fichier.url
        return None


class FicheAttachmentSerializer(serializers.ModelSerializer):
    kind_display = serializers.SerializerMethodField(read_only=True)
    file_url = serializers.SerializerMethodField(read_only=True)
    file_size = serializers.ReadOnlyField()
    file_extension = serializers.ReadOnlyField()
    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)

    class Meta:
        model = FicheAttachment
        fields = [
            "id",
            "fiche",
            "file",
            "file_url",
            "file_size",
            "file_extension",
            "kind",
            "kind_display",
            "note",
            "uploaded_by",
            "uploaded_by_username",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "file_url",
            "file_size",
            "file_extension",
            "kind_display",
            "uploaded_by",
            "uploaded_by_username",
            "created_at",
        ]

    @extend_schema_field(serializers.CharField())
    def get_kind_display(self, obj):
        return obj.get_kind_display()

    @extend_schema_field(serializers.URLField())
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class MedecinAvailabilitySerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.SerializerMethodField(read_only=True)
    consultation_type_display = serializers.SerializerMethodField(read_only=True)
    duration_formatted = serializers.ReadOnlyField()
    medecin_name = serializers.CharField(source="medecin.get_full_name", read_only=True)

    class Meta:
        model = MedecinAvailability
        fields = [
            "id",
            "medecin",
            "medecin_name",
            "day_of_week",
            "day_of_week_display",
            "start_time",
            "end_time",
            "consultation_type",
            "consultation_type_display",
            "duration_minutes",
            "duration_formatted",
            "is_active",
            "max_consultations",
            "location",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "duration_formatted", "medecin_name"]

    @extend_schema_field(serializers.CharField())
    def get_day_of_week_display(self, obj):
        return obj.get_day_of_week_display()

    @extend_schema_field(serializers.CharField())
    def get_consultation_type_display(self, obj):
        return obj.get_consultation_type_display()

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError({"end_time": "L'heure de fin doit être postérieure à l'heure de début"})

        if attrs["duration_minutes"] <= 0:
            raise serializers.ValidationError({"duration_minutes": "La durée doit être positive"})

        return attrs


class MedecinExceptionSerializer(serializers.ModelSerializer):
    exception_type_display = serializers.SerializerMethodField(read_only=True)
    medecin_name = serializers.CharField(source="medecin.get_full_name", read_only=True)

    class Meta:
        model = MedecinException
        fields = [
            "id",
            "medecin",
            "medecin_name",
            "start_datetime",
            "end_datetime",
            "exception_type",
            "exception_type_display",
            "reason",
            "is_recurring",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "medecin_name"]

    @extend_schema_field(serializers.CharField())
    def get_exception_type_display(self, obj):
        return obj.get_exception_type_display()

    def validate(self, attrs):
        if attrs["start_datetime"] >= attrs["end_datetime"]:
            raise serializers.ValidationError({"end_datetime": "La fin doit être postérieure au début"})
        return attrs


class WebhookEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.SerializerMethodField(read_only=True)
    processing_status_display = serializers.SerializerMethodField(read_only=True)
    related_user_name = serializers.CharField(source="related_user.username", read_only=True)
    related_fiche_number = serializers.CharField(source="related_fiche.numero_dossier", read_only=True)

    class Meta:
        model = WebhookEvent
        fields = [
            "id",
            "event_type",
            "event_type_display",
            "external_id",
            "sender_phone",
            "recipient_phone",
            "content",
            "raw_payload",
            "processing_status",
            "processing_status_display",
            "processing_error",
            "related_user",
            "related_user_name",
            "related_fiche",
            "related_fiche_number",
            "created_message",
            "received_at",
            "processed_at",
        ]
        read_only_fields = [
            "id",
            "received_at",
            "processed_at",
            "related_user_name",
            "related_fiche_number",
            "processing_status_display",
            "event_type_display",
        ]

    @extend_schema_field(serializers.CharField())
    def get_event_type_display(self, obj):
        return obj.get_event_type_display()

    @extend_schema_field(serializers.CharField())
    def get_processing_status_display(self, obj):
        return obj.get_processing_status_display()


class DataExportJobSerializer(serializers.ModelSerializer):
    export_format_display = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)
    duration = serializers.ReadOnlyField()
    file_size_formatted = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = DataExportJob
        fields = [
            "id",
            "created_by",
            "created_by_name",
            "export_format",
            "export_format_display",
            "date_start",
            "date_end",
            "include_personal_data",
            "filters",
            "status",
            "status_display",
            "file_path",
            "file_size",
            "file_size_formatted",
            "records_count",
            "error_message",
            "duration",
            "started_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "status",
            "file_path",
            "file_size",
            "records_count",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
            "duration",
            "file_size_formatted",
            "created_by_name",
            "status_display",
            "export_format_display",
        ]

    @extend_schema_field(serializers.CharField())
    def get_export_format_display(self, obj):
        return obj.get_export_format_display()

    @extend_schema_field(serializers.CharField())
    def get_status_display(self, obj):
        return obj.get_status_display()

    def validate(self, attrs):
        if attrs["date_start"] > attrs["date_end"]:
            raise serializers.ValidationError({"date_end": "La date de fin doit être postérieure à la date de début"})

        # Limiter la plage à 2 ans maximum
        from datetime import timedelta

        if (attrs["date_end"] - attrs["date_start"]) > timedelta(days=730):
            raise serializers.ValidationError({"date_end": "La plage d'export ne peut pas dépasser 2 ans"})

        return attrs


class CalendarSlotSerializer(serializers.Serializer):
    """Serializer pour les créneaux de calendrier générés."""

    datetime = serializers.DateTimeField()
    end_datetime = serializers.DateTimeField()
    available = serializers.BooleanField()
    consultation_type = serializers.CharField()
    location = serializers.CharField(allow_null=True)
    medecin_id = serializers.IntegerField()
    medecin_name = serializers.CharField()
    duration_minutes = serializers.IntegerField()
    max_consultations = serializers.IntegerField()
    booked_consultations = serializers.IntegerField()
