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
