from rest_framework import serializers


class AnalyseSymptomesRequestSerializer(serializers.Serializer):
    symptomes = serializers.CharField(help_text="Description libre des symptômes du patient.")
    conversation_id = serializers.IntegerField(required=False, help_text="ID conversation existante, sinon création.")


class AnalyseResultSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['pending', 'done'])
    response = serializers.CharField(allow_blank=True, required=False)
    cache_key = serializers.CharField()


class TaskStatusSerializer(serializers.Serializer):
    task_id = serializers.CharField()
    state = serializers.CharField()
    info = serializers.CharField(allow_blank=True, required=False)
