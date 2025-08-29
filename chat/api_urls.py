"""Routes API v1 de l'application chat.

Expose les ressources principales:
- /fiche-consultation/ : CRUD + actions (validate, relancer-analyse)
- /conversations/ : CRUD + action messages

Namespace: chat_api (utilisable pour reverse('chat_api:fiche-consultation-list')).
"""

from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .api_views import FicheConsultationViewSet, ConversationViewSet

app_name = 'chat_api'

router = DefaultRouter()
router.register(r'fiche-consultation', FicheConsultationViewSet, basename='fiche-consultation')
router.register(r'conversations', ConversationViewSet, basename='conversation')

urlpatterns = [path('', include(router.urls))]
from rest_framework.routers import DefaultRouter
from .api_views import (
    FicheConsultationViewSet,
    ConversationViewSet,
    MessageIAViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'consultations', FicheConsultationViewSet, basename='consultation')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageIAViewSet, basename='messageia')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = router.urls
