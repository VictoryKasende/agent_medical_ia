from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import FicheConsultation
from .distance_serializers import FicheConsultationDistanceSerializer
from .views import send_whatsapp_api

class RemoteConsultationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FicheConsultationDistanceSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Consultations Distance'],
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

    @extend_schema(tags=['Consultations Distance'], summary='Relancer analyse')
    @action(detail=True, methods=['post'], url_path='relancer')
    def relancer(self, request, pk=None):
        fiche = self.get_object()
        fiche.status = 'en_analyse'
        fiche.save()
        return Response({'detail': 'Analyse relancée', 'status': fiche.status})

    @extend_schema(tags=['WhatsApp'], summary='Envoyer template WhatsApp')
    @action(detail=True, methods=['post'], url_path='send-whatsapp')
    def send_whatsapp(self, request, pk=None):
        fiche = self.get_object()
        success, result = send_whatsapp_api(fiche.telephone, None, fiche=fiche)
        if success:
            return Response({'detail': 'Message envoyé', 'info': result})
        return Response({'detail': 'Envoi échoué', 'error': result}, status=500)

    send_whatsapp.throttle_scope = 'remote-consultation-send'
