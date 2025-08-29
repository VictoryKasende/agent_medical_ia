from rest_framework import viewsets, serializers, permissions
from .models import FicheConsultation

class DistanceConsultationSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = FicheConsultation
        fields = [
            'id', 'nom', 'prenom', 'age', 'created_at', 'status', 'status_display',
            'motif_consultation', 'temperature', 'tension_arterielle', 'pouls', 'spo2',
            'histoire_maladie', 'diagnostic_ia'
        ]

    def get_status_display(self, obj):  # pragma: no cover - simple mapping
        return obj.get_status_display()

class IsMedecinOrReadOnly(permissions.BasePermission):
    """Autorise lecture à tout utilisateur authentifié; écriture réservée aux médecins (future extension)."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # Placeholder pour future logique (ex: role == 'medecin')
        return getattr(request.user, 'role', None) == 'medecin'

class DistanceConsultationViewSet(viewsets.ReadOnlyModelViewSet):
    """Liste/lecture des consultations à distance pour consommation front progressive.
    Filtrage possible par ?status=...
    """
    serializer_class = DistanceConsultationSerializer
    permission_classes = [IsMedecinOrReadOnly]

    def get_queryset(self):
        qs = FicheConsultation.objects.filter(is_patient_distance=True).order_by('-created_at')
        status_value = self.request.query_params.get('status')
        if status_value:
            qs = qs.filter(status=status_value)
        return qs
