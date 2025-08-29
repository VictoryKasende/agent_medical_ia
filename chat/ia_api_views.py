import hashlib
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from celery.result import AsyncResult

from authentication.permissions import IsMedecin
from .models import Conversation, MessageIA
from .tasks import analyse_symptomes_task
from .ia_serializers import (
    AnalyseSymptomesRequestSerializer,
    AnalyseResultSerializer,
    TaskStatusSerializer,
)


class StartAnalyseAPIView(APIView):
    permission_classes = [IsAuthenticated, IsMedecin]
    throttle_scope = 'ia-analyse'
    throttle_classes = [ScopedRateThrottle]
    # Pour drf-spectacular: requête / réponse principales
    request_serializer = AnalyseSymptomesRequestSerializer
    response_serializer = AnalyseResultSerializer  # réponse initiale (pending)

    def post(self, request):
        serializer = AnalyseSymptomesRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        symptomes = data['symptomes']
        if 'conversation_id' in data:
            conversation = get_object_or_404(Conversation, id=data['conversation_id'])
        else:
            conversation = Conversation.objects.create(user=request.user)

        # Message utilisateur sauvegardé avant la tâche
        MessageIA.objects.create(conversation=conversation, role='user', content=symptomes)

        hash_key = hashlib.md5(symptomes.encode('utf-8')).hexdigest()
        cache_key = f"diagnostic_{hash_key}"
        cached = cache.get(cache_key)
        if cached:
            return Response({
                'already_cached': True,
                'cache_key': cache_key,
                'status': 'done',
                'response': cached,
            })

        # Lancement tâche après commit pour éviter race conditions si future transaction
        def launch_task():
            analyse_symptomes_task.delay(symptomes, request.user.id, conversation.id, cache_key)

        transaction.on_commit(launch_task)

        return Response({
            'task_id': None,  # On ne récupère pas l'id quand lancé via callback différé
            'cache_key': cache_key,
            'status': 'pending'
        }, status=status.HTTP_202_ACCEPTED)


class TaskStatusAPIView(APIView):
    permission_classes = [IsAuthenticated, IsMedecin]
    throttle_scope = 'ia-status'
    throttle_classes = [ScopedRateThrottle]
    response_serializer = TaskStatusSerializer

    def get(self, request, task_id):
        result = AsyncResult(task_id)
        payload = {
            'task_id': task_id,
            'state': result.state,
        }
        if result.state == 'FAILURE':
            payload['info'] = str(result.info)
        elif result.info:
            payload['info'] = str(result.info)
        return Response(TaskStatusSerializer(payload).data)


class AnalyseResultAPIView(APIView):
    permission_classes = [IsAuthenticated, IsMedecin]
    throttle_scope = 'ia-result'
    throttle_classes = [ScopedRateThrottle]
    response_serializer = AnalyseResultSerializer

    def get(self, request):
        cache_key = request.query_params.get('cache_key')
        if not cache_key:
            return Response({'detail': 'cache_key requis'}, status=400)
        cached = cache.get(cache_key)
        if cached:
            data = {'status': 'done', 'response': cached, 'cache_key': cache_key}
        else:
            data = {'status': 'pending', 'response': '', 'cache_key': cache_key}
        return Response(AnalyseResultSerializer(data).data)
