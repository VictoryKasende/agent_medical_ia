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

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import MedecinViewSet, UserRegisterAPIView, UserViewSet
from .jwt_views import PublicTokenObtainPairView as TokenObtainPairView
from .jwt_views import PublicTokenRefreshView as TokenRefreshView
from .jwt_views import PublicTokenVerifyView as TokenVerifyView
from .jwt_views import (
    csrf_token_view,
)
from .views_api import LogoutView, MeView  # legacy style views (logout, me) if still used

app_name = "auth_api"

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("medecins", MedecinViewSet, basename="medecin")

urlpatterns = [
    # CSRF token pour les clients JavaScript
    path("csrf/", csrf_token_view, name="csrf_token"),
    # JWT core
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("jwt/token/", TokenObtainPairView.as_view(), name="token_obtain_pair_alias"),  # Alias pour frontend
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Session-aware / auxiliary
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    # Users
    path("users/register/", UserRegisterAPIView.as_view(), name="user-register"),
    path("", include(router.urls)),
]
