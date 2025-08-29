from rest_framework.routers import DefaultRouter
from django.urls import path
from .distance_api_views import RemoteConsultationViewSet, WhatsAppInboundWebhookView

router = DefaultRouter()
router.register(r'consultations-distance', RemoteConsultationViewSet, basename='consultation-distance')

urlpatterns = router.urls + [
    path('whatsapp/webhook/', WhatsAppInboundWebhookView.as_view(), name='whatsapp-inbound-webhook'),
]
