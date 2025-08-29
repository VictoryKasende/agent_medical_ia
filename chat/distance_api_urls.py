from rest_framework.routers import DefaultRouter
from django.urls import path
from .distance_api_views import DistanceConsultationViewSet

router = DefaultRouter()
router.register(r'consultations-distance', DistanceConsultationViewSet, basename='consultations-distance')

urlpatterns = router.urls

# Exemple futur: webhook / whatsapp
# from .distance_api_views import WhatsAppInboundWebhookView
# urlpatterns += [ path('whatsapp/webhook/', WhatsAppInboundWebhookView.as_view()) ]
