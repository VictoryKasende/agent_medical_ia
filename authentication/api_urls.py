"""Authentication API urls (JWT + users) - Cleaned after merge conflicts.

Exposed endpoints base path: /api/v1/auth/
- token/ (POST) obtain pair
- refresh/ (POST) refresh token
- verify/ (POST) verify token
- logout/ (POST) blacklist refresh (if enabled)
- users/register/ (POST) public registration (optionnel selon politique)
- users/ (CRUD) restricted (self or admin)
- users/me/ (GET/PATCH) self profile
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .jwt_views import (
    PublicTokenObtainPairView as TokenObtainPairView,
    PublicTokenRefreshView as TokenRefreshView,
    PublicTokenVerifyView as TokenVerifyView,
)

from .views_api import LogoutView, MeView  # legacy style views (logout, me) if still used
from .api_views import UserRegisterAPIView, UserViewSet, MedecinViewSet

app_name = 'auth_api'

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('medecins', MedecinViewSet, basename='medecin')

urlpatterns = [
    # JWT core
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Session-aware / auxiliary
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    # Users
    path('users/register/', UserRegisterAPIView.as_view(), name='user-register'),
    path('', include(router.urls)),
]


