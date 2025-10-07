from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import FicheConsultation


class DistanceConsultationSerializer(serializers.ModelSerializer):
    # Extension (migration étape 8): ajout champs cephalees, febrile, telephone + mapping booléen
    status_display = serializers.SerializerMethodField()
    febrile_bool = serializers.SerializerMethodField(help_text="True si febrile == 'Oui'")

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
            # Symptômes / anamnèse ciblés pour la vue distance
            "motif_consultation",
            "histoire_maladie",
            "cephalees",
            "febrile",
            "febrile_bool",
            # Signes vitaux principaux
            "temperature",
            "tension_arterielle",
            "pouls",
            "spo2",
            # IA
            "diagnostic_ia",
        ]

    def get_status_display(self, obj):  # pragma: no cover - simple mapping
        return obj.get_status_display()

    def get_febrile_bool(self, obj):  # pragma: no cover - simple mapping
        return True if getattr(obj, "febrile", None) == "Oui" else False


class IsMedecinOrReadOnly(permissions.BasePermission):
    """Autorise lecture à tout utilisateur authentifié; écriture réservée aux médecins (future extension)."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # Placeholder pour future logique (ex: role == 'medecin')
        return getattr(request.user, "role", None) == "medecin"


class DistanceConsultationViewSet(viewsets.ReadOnlyModelViewSet):
    """Liste/lecture des consultations à distance pour consommation front progressive.
    Filtrage possible par ?status=...
    """

    serializer_class = DistanceConsultationSerializer
    permission_classes = [IsMedecinOrReadOnly]

    def get_queryset(self):
        qs = FicheConsultation.objects.filter(is_patient_distance=True).order_by("-created_at")
        status_value = self.request.query_params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)
        return qs

    @extend_schema(tags=["Consultations Distance"], summary="Valider consultation distance")
    @action(detail=True, methods=["post"], url_path="validate")
    def validate(self, request, pk=None):
        fiche = self.get_object()
        if fiche.status not in ["en_analyse", "analyse_terminee"]:
            return Response({"detail": "Statut incompatible"}, status=400)
        fiche.status = "valide_medecin"
        fiche.date_validation = timezone.now()
        fiche.medecin_validateur = request.user
        fiche.save()
        return Response(DistanceConsultationSerializer(fiche, context={"request": request}).data)

    @extend_schema(tags=["Consultations Distance"], summary="Relancer analyse IA")
    @action(detail=True, methods=["post"], url_path="relancer")
    def relancer(self, request, pk=None):
        fiche = self.get_object()
        fiche.status = "en_analyse"
        fiche.save()
        return Response({"detail": "Analyse relancée", "status": fiche.status})
