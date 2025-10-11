"""
URL configuration for agent_medical_ia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from chat.ia_api_views import AnalyseResultAPIView, StartAnalyseAPIView, TaskStatusAPIView
from chat.models import FicheConsultation
from chat.serializers import FicheConsultationDistanceSerializer


class DeprecatedConsultationsDistanceAPIView(APIView):
    """Deprecated list-only endpoint kept for backward compatibility.

    NOTE: Will be removed in a future release. Use
        /api/v1/fiche-consultation/?is_patient_distance=true
    instead. A deprecation header is added to responses.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FicheConsultationDistanceSerializer(many=True)})
    def get(self, request):  # list only
        qs = FicheConsultation.objects.filter(is_patient_distance=True).order_by("-created_at")
        serializer = FicheConsultationDistanceSerializer(qs, many=True)
        return Response(
            serializer.data,
            headers={
                "X-Deprecated": "true",
                "Link": '</api/v1/fiche-consultation/?is_patient_distance=true>; rel="successor-version"',
            },
        )


urlpatterns = [
    # Legacy HTML (progressive migration). Keep only one include.
    path("", include("chat.urls")),
    # Admin & classic auth (HTML forms)
    path("admin/", admin.site.urls),
    path("auth/", include("authentication.urls")),
    # Core API v1
    path("api/v1/", include("chat.api_urls")),
    path("api/v1/auth/", include("authentication.api_urls")),
    # Alias déprécié (sera retiré) pour ancienne route consultations-distance
    path(
        "api/v1/consultations-distance/",
        DeprecatedConsultationsDistanceAPIView.as_view(),
        name="consultations_distance_deprecated",
    ),
    # JWT convenience (non-versioned) – optional; could be deprecated later
    path("api/auth/jwt/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/jwt/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # IA async endpoints (kept outside versioning for now; consider moving under v1/ia/)
    path("api/ia/analyse/", StartAnalyseAPIView.as_view(), name="ia_start"),
    path("api/ia/status/<str:task_id>/", TaskStatusAPIView.as_view(), name="ia_status"),
    path("api/ia/result/", AnalyseResultAPIView.as_view(), name="ia_result"),
    # OpenAPI / Swagger / Redoc
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
