from rest_framework.routers import DefaultRouter
from django.urls import path
from .distance_api_views import RemoteConsultationViewSet, WhatsAppInboundWebhookView
from .distance_api_views import RemoteConsultationViewSet
from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

class WhatsAppInboundWebhookView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(tags=['WhatsApp'], summary='Webhook inbound WhatsApp')
    def post(self, request, *args, **kwargs):
        payload = request.data if isinstance(request.data, dict) else {}
        return Response({'received': True, 'payload_keys': list(payload.keys())})

router = DefaultRouter()
router.register(r'consultations-distance', RemoteConsultationViewSet, basename='consultation-distance')

urlpatterns = router.urls + [
    path('whatsapp/webhook/', WhatsAppInboundWebhookView.as_view(), name='whatsapp-inbound-webhook'),
]
