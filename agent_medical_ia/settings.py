"""Base Django settings for agent_medical_ia (Django 4.2).

Nettoyage post-merge:
- Suppression des doublons INSTALLED_APPS / REST_FRAMEWORK / SPECTACULAR_SETTINGS
- Unification de la configuration DRF avec option de cohabitation (session + JWT)
"""

import os
from datetime import timedelta
from pathlib import Path
import sys
import dotenv
import dj_database_url

dotenv.load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-gs#ncc0tx4ai(+$5y&w5&9q@&^(nigk4!t_xe(6mf4*%dc2gjf'
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "OhcmqJJ6ODIGo6Z2TyR£S~:afl2#4~*V")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG_VALUE = os.getenv("DEBUG", "False")
DEBUG = DEBUG_VALUE.lower() in ['true', '1', 'yes', 'on']

# ALLOWED_HOSTS configuration (plus permissif pour Docker)
ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,*')
if ALLOWED_HOSTS_ENV == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ALLOWED_HOSTS_ENV.split(',')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # API / Auth / Docs
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    # Domain apps
    'authentication',
    'chat',
]

API_COHAB_ENABLED = os.getenv('API_COHAB_ENABLED', 'true').lower() in ['1','true','yes','on']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'agent_medical_ia.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'chat.context_processors.deprecation_banner',  # Ajout bannière de dépréciation
            ],
        },
    },
]

REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')

# Détection tests avant toute logique dépendante
RUNNING_TESTS = (
    'PYTEST_CURRENT_TEST' in os.environ
    or any(arg.endswith('pytest') or arg == 'pytest' for arg in sys.argv)
    or any(arg in sys.argv for arg in ['test'])
)  # détection améliorée

if RUNNING_TESTS or os.getenv('FORCE_LOCAL_CACHE', '').lower() in ['1','true','yes']:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache'
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }

WSGI_APPLICATION = 'agent_medical_ia.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "False") == "True"

# --- Database configuration -------------------------------------------------
# Règles:
# 1. Si DEVELOPMENT_MODE=True => SQLite locale.
# 2. Si on exécute les tests (pytest ou manage.py test) => SQLite locale pour éviter
#    dépendance à DATABASE_URL en CI locale.
# 3. Sinon, en production / autre commande: on exige DATABASE_URL.
# (déjà défini plus haut pour pouvoir configurer les caches)

if DEVELOPMENT_MODE or RUNNING_TESTS:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
else:
    if len(sys.argv) > 1 and sys.argv[1] == 'collectstatic':  # évite erreur build collectstatic
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
            }
        }
    else:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise Exception("DATABASE_URL environment variable not defined and not in DEVELOPMENT_MODE/test context")
        DATABASES = {
            "default": dj_database_url.parse(db_url),
        }

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,
        }
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
AUTH_USER_MODEL = 'authentication.CustomUser'
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Paris'

# Exécution synchrone des tâches Celery pendant les tests
if RUNNING_TESTS:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# Configuration CSRF pour Docker
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000',
]

# Permettre les cookies CSRF
CSRF_COOKIE_SECURE = False  # True en production avec HTTPS
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False

# =============================
# DRF & API Configuration (unifiée)
# =============================

BASE_THROTTLES = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
]

BASE_THROTTLE_RATES = {
    'anon': '30/min',
    'user': '300/min',
    # Scopes spécifiques
    'validate-consultation': '30/hour',
    'relancer-analyse': '10/hour',
    'conversation-messages': '120/min',
    'remote-consultation-send': '20/hour',
    # IA scopes
    'ia-analyse': '30/hour',
    'ia-status': '300/hour',
    'ia-result': '300/hour',
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': BASE_THROTTLES,
    'DEFAULT_THROTTLE_RATES': BASE_THROTTLE_RATES,
}

if API_COHAB_ENABLED:
    # Ajoute l'authentification session pour les templates legacy qui consomment l'API
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Agent Medical IA API',
    'DESCRIPTION': 'API REST (consultations, conversations IA, authentification, actions médicales).',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': 'Consultations', 'description': 'CRUD & actions sur les fiches de consultation.'},
        {'name': 'Conversations', 'description': 'Discussions IA et messages.'},
        {'name': 'Auth', 'description': 'Authentification & JWT.'},
    ],
    'COMPONENT_SPLIT_REQUEST': True,
}

