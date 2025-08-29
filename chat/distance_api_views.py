from rest_framework import viewsets, status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import FicheConsultation
from .distance_serializers import FicheConsultationDistanceSerializer
from authentication.permissions import IsMedecinOrAdmin
from .views import send_whatsapp_api
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import json


class RemoteConsultationViewSet(viewsets.ReadOnlyModelViewSet):
    """Consultations à distance: list / retrieve + actions médicales."""
from .views import send_whatsapp_api

class RemoteConsultationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FicheConsultationDistanceSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Consultations Distance'],
        summary='Lister les consultations à distance',
        description='Renvoie la liste des fiches de consultation marquées comme distance. Filtrage possible via le paramètre status.',
        parameters=[
            OpenApiParameter(name='status', location=OpenApiParameter.QUERY, required=False, description='Filtrer par statut interne', type=str)
        ],
        responses={200: OpenApiResponse(response=FicheConsultationDistanceSerializer, description='Liste de consultations')}
        summary='Lister les consultations distance',
        parameters=[OpenApiParameter(name='status', location=OpenApiParameter.QUERY, required=False, description='Filtrer par statut', type=str)],
        responses={200: OpenApiResponse(response=FicheConsultationDistanceSerializer, description='Liste')}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = FicheConsultation.objects.filter(is_patient_distance=True).order_by('-created_at')
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def get_permissions(self):
        if self.action in ['validate', 'relancer', 'send_whatsapp']:
            return [IsMedecinOrAdmin()]
        return super().get_permissions()

    @extend_schema(
        tags=['Consultations Distance'],
        summary='Valider une consultation',
        description='Valide médicalement une fiche et enregistre la date + médecin validateur.',
        responses={200: FicheConsultationDistanceSerializer}
    )
    @extend_schema(tags=['Consultations Distance'], summary='Valider consultation')
    @action(detail=True, methods=['post'], url_path='validate')
    def validate(self, request, pk=None):
        fiche = self.get_object()
        if fiche.status not in ['en_analyse', 'analyse_terminee']:
            return Response({'detail': 'Statut incompatible'}, status=400)
        fiche.status = 'valide_medecin'
        fiche.date_validation = timezone.now()
        fiche.medecin_validateur = request.user
        fiche.save()
        return Response(self.get_serializer(fiche).data)

    @extend_schema(
        tags=['Consultations Distance'],
        summary='Relancer analyse IA',
        description='Replace la fiche en statut en_analyse pour relancer une analyse IA externe.',
        responses={200: OpenApiResponse(description='Analyse relancée')}
    )
    @extend_schema(tags=['Consultations Distance'], summary='Relancer analyse')
    @action(detail=True, methods=['post'], url_path='relancer')
    def relancer(self, request, pk=None):
        fiche = self.get_object()
        fiche.status = 'en_analyse'
        fiche.save()
        return Response({'detail': 'Analyse relancée', 'status': fiche.status})

    @extend_schema(
        tags=['WhatsApp'],
        summary='Envoyer un template WhatsApp',
        description='Envoie un template WhatsApp (Twilio) au patient lié à la fiche. Throttling appliqué.',
        responses={200: OpenApiResponse(description='Message envoyé'), 500: OpenApiResponse(description='Erreur envoi')}
    )
    @extend_schema(tags=['WhatsApp'], summary='Envoyer template WhatsApp')
    @action(detail=True, methods=['post'], url_path='send-whatsapp')
    def send_whatsapp(self, request, pk=None):
        fiche = self.get_object()
        success, result = send_whatsapp_api(fiche.telephone, None, fiche=fiche)
        if success:
            return Response({'detail': 'Message envoyé', 'info': result})
        return Response({'detail': 'Envoi échoué', 'error': result}, status=500)

    # Assigner dynamiquement le scope de throttling pour cette action
    send_whatsapp.throttle_scope = 'remote-consultation-send'


class WhatsAppInboundWebhookView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(tags=['WhatsApp'], summary='Webhook inbound WhatsApp', description='Réception des statuts/messages entrants Twilio WhatsApp (signature à implémenter).')
    def post(self, request, *args, **kwargs):
        payload = request.data if isinstance(request.data, dict) else {}
        # TODO: vérifier signature X-Twilio-Signature (sécurité) avant traitement
        # Log minimal / future persistance
        return Response({'received': True, 'payload_keys': list(payload.keys())})
    send_whatsapp.throttle_scope = 'remote-consultation-send'
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
