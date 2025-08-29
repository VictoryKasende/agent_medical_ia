"""Routes API v1 de l'application chat (version unifiée après refonte).

Endpoints exposés:
 - /fiche-consultation/ : CRUD fiches + actions validate / relancer
     * Vue "distance" fusionnée: ajouter `?is_patient_distance=true` (serializer léger)
 - /conversations/      : CRUD conversations + /{id}/messages/
 - /messages/ (lecture) : Accès direct messages IA (list/retrieve)
 - /users/ (lecture)    : Lecture utilisateurs (staff/admin scope list)

Important: Ce module NE doit contenir qu'un seul router.
"""

from rest_framework.routers import DefaultRouter
from .api_views import (
    FicheConsultationViewSet,
    ConversationViewSet,
    MessageIAViewSet,
    UserViewSet,
)

app_name = 'chat_api'

router = DefaultRouter()
router.register(r'fiche-consultation', FicheConsultationViewSet, basename='fiche-consultation')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageIAViewSet, basename='messageia')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = router.urls
