from rest_framework import serializers


class AnalyseSymptomesRequestSerializer(serializers.Serializer):
    symptomes = serializers.CharField(help_text="Description libre des symptômes du patient.")
    conversation_id = serializers.IntegerField(required=False, help_text="ID conversation existante, sinon création.")


class AnalyseResultSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["pending", "done"], help_text="État de l'analyse")
    response = serializers.CharField(allow_blank=True, required=False, help_text="Résultat de l'analyse IA")
    cache_key = serializers.CharField(help_text="Clé de cache utilisée pour récupérer le résultat")


class TaskStatusSerializer(serializers.Serializer):
    task_id = serializers.CharField(help_text="ID de la tâche Celery")
    state = serializers.CharField(help_text="État de la tâche")
    info = serializers.CharField(allow_blank=True, required=False, help_text="Information ou erreur de la tâche")
