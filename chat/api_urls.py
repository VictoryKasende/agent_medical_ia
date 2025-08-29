from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .api_views import FicheConsultationViewSet

router = DefaultRouter()
# Route demandée: /api/v1/fiche-consultation/
router.register(r'fiche-consultation', FicheConsultationViewSet, basename='fiche-consultation')

urlpatterns = [
    path('', include(router.urls)),
]
