from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import UserRegisterAPIView, UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('users/register/', UserRegisterAPIView.as_view(), name='user-register'),
    path('', include(router.urls)),
]


