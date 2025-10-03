# Settings pour tests CI/CD
from .settings import *
import os

# Utiliser SQLite pour les tests si PostgreSQL échoue
if 'GITHUB_ACTIONS' in os.environ:
    # Configuration base de données test
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
    
    # Désactiver Celery pour les tests
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    
    # Désactiver cache Redis pour les tests
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    
    # Logs simplifiés
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    }
    
    # API keys factices pour tests
    OPENAI_API_KEY = "test-key"
    ANTHROPIC_API_KEY = "test-key"
    GOOGLE_API_KEY = "test-key"
    TWILIO_ACCOUNT_SID = "test-sid"
    TWILIO_AUTH_TOKEN = "test-token"
    TWILIO_PHONE_NUMBER = "+1234567890"

# Variables requises pour les tests
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'test-secret-key-for-ci-cd-only')
DEBUG = True
ALLOWED_HOSTS = ['*']