"""Base Django settings for agent_medical_ia (Django 4.2)."""

import os
import sys
from datetime import timedelta
from pathlib import Path

import dj_database_url
import dotenv

dotenv.load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Secret key
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "default-secret-key")

# Debug
DEBUG = os.getenv("DEBUG", "False").lower() in ["true", "1", "yes", "on"]

# Allowed hosts
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")

# Apps
INSTALLED_APPS = [
    "jazzmin",  # Dashboard admin professionnel (doit être AVANT django.contrib.admin)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "authentication",
    "chat",
]


API_COHAB_ENABLED = os.getenv("API_COHAB_ENABLED", "true").lower() in ["1", "true", "yes", "on"]

# Middleware
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Doit être en premier
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "agent_medical_ia.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Redis / Cache
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1")
RUNNING_TESTS = (
    "PYTEST_CURRENT_TEST" in os.environ
    or any(arg.endswith("pytest") or arg == "pytest" for arg in sys.argv)
    or "test" in sys.argv
)
if RUNNING_TESTS or os.getenv("FORCE_LOCAL_CACHE", "").lower() in ["1", "true", "yes"]:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "test-cache"}}
else:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }

WSGI_APPLICATION = "agent_medical_ia.wsgi.application"

# Database
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "False") == "True"
if DEVELOPMENT_MODE or RUNNING_TESTS:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
else:
    if len(sys.argv) > 1 and sys.argv[1] == "collectstatic":
        DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
    else:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise Exception("DATABASE_URL not defined")
        DATABASES = {"default": dj_database_url.parse(db_url)}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 4}},
]

# Internationalization
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Lubumbashi"  # Heure locale Congo (Lubumbashi)
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Custom User
AUTH_USER_MODEL = "authentication.CustomUser"
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/auth/login/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Celery
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Paris"
CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "300"))
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "240"))
if RUNNING_TESTS:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# CSRF pour tests / Docker / Frontend
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "http://localhost:5173",  # Frontend Vite/React/Vue
    "http://127.0.0.1:5173",
]
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False

# DRF
BASE_THROTTLES = [
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
]
BASE_THROTTLE_RATES = {
    "anon": "30/min",
    "user": "300/min",
    "validate-consultation": "30/hour",
    "relancer-analyse": "10/hour",
    "conversation-messages": "120/min",
    "remote-consultation-send": "20/hour",
    "ia-analyse": "30/hour",
    "ia-status": "300/hour",
    "ia-result": "300/hour",
}
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": BASE_THROTTLES,
    "DEFAULT_THROTTLE_RATES": BASE_THROTTLE_RATES,
}
if API_COHAB_ENABLED:
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    )

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),  # Augmenté pour le développement
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "Agent Medical IA API",
    "DESCRIPTION": "API REST (consultations, conversations IA, authentification, actions médicales).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "Consultations", "description": "CRUD & actions sur les fiches de consultation."},
        {"name": "Conversations", "description": "Discussions IA et messages."},
        {"name": "Auth", "description": "Authentification & JWT."},
        {"name": "Rendez-vous", "description": "Prise et gestion des rendez-vous."},
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    # Évite les collisions de noms d'enum et fournit des noms stables/explicites
    "ENUM_NAME_OVERRIDES": {
        # Format attendu: module_path.Model.field (chemin importable réel)
        "authentication.models.CustomUser.role": "UserRoleEnum",
        "chat.models.MessageIA.role": "MessageRoleEnum",
        # Fréquences partagées (tabac/alcool/activite_physique)
        "chat.models.FicheConsultation.alcool": "LifestyleFrequencyEnum",
        "chat.models.FicheConsultation.tabac": "LifestyleFrequencyEnum",
        "chat.models.FicheConsultation.activite_physique": "LifestyleFrequencyEnum",
        # Capacités (mêmes choices pour physique/psychologique)
        "chat.models.FicheConsultation.capacite_physique": "CapacityEnum",
        "chat.models.FicheConsultation.capacite_psychologique": "CapacityEnum",
        # Colorations (mêmes choices Normale/Anormale)
        "chat.models.FicheConsultation.coloration_palpebrale": "ColorationEnum",
        "chat.models.FicheConsultation.coloration_bulbaire": "ColorationEnum",
        # Statuts distincts
        "chat.models.FicheConsultation.status": "ConsultationStatusEnum",
        "chat.models.Appointment.status": "AppointmentStatusEnum",
    },
    "POSTPROCESSING_HOOKS": ["chat.schema_hooks.unify_enum_names"],
}

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()  # Filtrer les chaînes vides
]

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Autorise toutes les origines en mode DEBUG

# Configuration CORS pour JWT et CSRF
CORS_ALLOW_CREDENTIALS = True  # Permet l'envoi de cookies/credentials
CORS_ALLOWED_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",  # Header CSRF
    "x-requested-with",
]

# Configuration CORS explicite pour le frontend
if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# =============================================================================
# JAZZMIN - Configuration Dashboard Admin Professionnel
# =============================================================================

JAZZMIN_SETTINGS = {
    # Titre du site
    "site_title": "Agent Médical IA",
    "site_header": "Agent Médical IA",
    "site_brand": "Agent Médical IA",
    "site_logo": None,  # Optionnel: "images/logo.png"
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    
    # Message de bienvenue
    "welcome_sign": "Bienvenue sur la plateforme Agent Médical IA",
    "copyright": "Agent Médical IA © 2026",
    
    # Recherche de modèles
    "search_model": ["auth.User", "chat.FicheConsultation"],
    
    # Utilisateur en haut
    "user_avatar": None,
    
    # Liens du menu supérieur
    "topmenu_links": [
        {"name": "Accueil", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "API Docs", "url": "/api/v1/docs/", "new_window": True},
        {"model": "auth.User"},
        {"app": "chat"},
    ],
    
    # Afficher le menu latéral
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    
    # Ordre des apps dans le menu
    "order_with_respect_to": [
        "auth",
        "authentication",
        "chat",
    ],
    
    # Icônes personnalisées pour les apps/modèles
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "authentication": "fas fa-shield-alt",
        "authentication.customuser": "fas fa-user-md",
        "authentication.patientprofile": "fas fa-user-injured",
        "authentication.medecinprofile": "fas fa-stethoscope",
        "chat": "fas fa-comments-medical",
        "chat.ficheconsultation": "fas fa-file-medical",
        "chat.conversation": "fas fa-comments",
        "chat.messageia": "fas fa-robot",
        "chat.appointment": "fas fa-calendar-check",
        "chat.fichemessage": "fas fa-envelope",
        "chat.fichereference": "fas fa-book-medical",
        "chat.labresult": "fas fa-flask",
        "chat.ficheattachment": "fas fa-paperclip",
        "chat.medecinAvailability": "fas fa-clock",
        "chat.medecinexception": "fas fa-calendar-times",
        "chat.webhookevent": "fas fa-satellite-dish",
        "chat.dataexportjob": "fas fa-file-export",
    },
    
    # Icône par défaut
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    
    # Liens personnalisés dans le menu
    "custom_links": {
        "chat": [{
            "name": "📊 Statistiques",
            "url": "admin:index",
            "icon": "fas fa-chart-bar",
            "permissions": ["chat.view_ficheconsultation"]
        }]
    },
    
    # UI Tweaks
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    
    # Changelist formats
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
        "chat.ficheconsultation": "horizontal_tabs",
    },
}

# Configuration UI Jazzmin
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
