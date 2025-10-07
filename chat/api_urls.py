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
    AppointmentViewSet,
    ConversationViewSet,
    DataExportJobViewSet,
    FicheAttachmentViewSet,
    FicheConsultationViewSet,
    FicheReferenceViewSet,
    LabResultViewSet,
    MedecinAvailabilityViewSet,
    MedecinExceptionViewSet,
    MessageIAViewSet,
    UserViewSet,
    WebhookEventViewSet,
)

app_name = "chat_api"

router = DefaultRouter()
router.register(r"fiche-consultation", FicheConsultationViewSet, basename="fiche-consultation")
router.register(r"conversations", ConversationViewSet, basename="conversation")
router.register(r"messages", MessageIAViewSet, basename="messageia")
router.register(r"users", UserViewSet, basename="user")
router.register(r"appointments", AppointmentViewSet, basename="appointment")
router.register(r"references", FicheReferenceViewSet, basename="reference")
router.register(r"lab-results", LabResultViewSet, basename="lab-result")
router.register(r"attachments", FicheAttachmentViewSet, basename="attachment")

# Nouvelles routes P1
router.register(r"availabilities", MedecinAvailabilityViewSet, basename="availability")
router.register(r"exceptions", MedecinExceptionViewSet, basename="exception")
router.register(r"webhooks", WebhookEventViewSet, basename="webhook")
router.register(r"exports", DataExportJobViewSet, basename="export")

urlpatterns = router.urls
