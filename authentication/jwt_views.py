"""JWT views sans CSRF (désactivent SessionAuthentication).

Contexte:
    Avec API_COHAB_ENABLED activé nous avons ajouté SessionAuthentication
    globalement. Les vues SimpleJWT utilisent alors SessionAuthentication en
    premier et imposent un contrôle CSRF sur les POST anonymes (obtain / refresh)
    ce qui retourne 403 quand le client (Postman, curl) n'envoie pas de cookie CSRF.

Solution:
    Sous-classer les vues et vider authentication_classes pour qu'elles soient
    purement stateless. Permission AllowAny conservée.
"""

from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


class PublicTokenObtainPairView(TokenObtainPairView):
    authentication_classes: list = []  # type: ignore[assignment]
    permission_classes = [AllowAny]


class PublicTokenRefreshView(TokenRefreshView):
    authentication_classes: list = []  # type: ignore[assignment]
    permission_classes = [AllowAny]


class PublicTokenVerifyView(TokenVerifyView):
    authentication_classes: list = []  # type: ignore[assignment]
    permission_classes = [AllowAny]
