from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .api_views import ConversationViewSet

router = DefaultRouter()
router.register('conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
]
