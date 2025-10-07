"""(Deprecated) Legacy distance consultations API routes.

Historique:
 - Ce fichier contenait des doublons de router/register et une tentative d'ajout de webhook WhatsApp.
 - La version refonte expose désormais les consultations distance via `/api/v1/consultations-distance/`
     (voir `DistanceConsultationViewSet` dans `distance_api_views.py`).
 - Ce module n'est plus inclus dans `agent_medical_ia/urls.py` et est conservé uniquement comme repère
     jusqu'à suppression définitive (plan de dépréciation MIGRATION_DEPRECATION.md).

Action future:
 - Supprimer ce fichier après confirmation que plus aucun import externe ne l'utilise.
"""

from rest_framework.routers import DefaultRouter  # pragma: no cover - legacy

from .distance_api_views import DistanceConsultationViewSet  # pragma: no cover - legacy

router = DefaultRouter()
router.register(r"consultations-distance", DistanceConsultationViewSet, basename="consultations-distance")

# Expose variable attendue par Django même si non utilisée.
urlpatterns = router.urls  # pragma: no cover
