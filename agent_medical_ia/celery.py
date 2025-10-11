import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_medical_ia.settings")

app = Celery("agent_medical_ia")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
