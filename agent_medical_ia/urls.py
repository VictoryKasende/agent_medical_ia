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
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf.urls.static import static
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from chat.ia_api_views import StartAnalyseAPIView, TaskStatusAPIView, AnalyseResultAPIView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from chat.distance_api_urls import urlpatterns as distance_api_urls

urlpatterns = [
    path('', include('chat.urls')),
    path('', include('chat.urls')),  # Legacy HTML
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    # API v1
    path('api/v1/', include('chat.api_urls')),
    path('api/v1/auth/', include('authentication.api_urls')),
    # OpenAPI / Docs (unique)
    path('api/v1/', include('authentication.api_urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/', include('chat.api_urls')),
    # API: schema & documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # JWT auth
    path('api/auth/jwt/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # API schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # JWT
    path('api/auth/jwt/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # IA async
    path('api/ia/analyse/', StartAnalyseAPIView.as_view(), name='ia_start'),
    path('api/ia/status/<str:task_id>/', TaskStatusAPIView.as_view(), name='ia_status'),
    path('api/ia/result/', AnalyseResultAPIView.as_view(), name='ia_result'),
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    path('', include('chat.urls')),

    # JWT
    path('api/auth/jwt/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Schema & Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1
    path('api/v1/', include(distance_api_urls)),
]

if getattr(settings, 'API_COHAB_ENABLED', False):
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
    try:
        from chat.distance_api_urls import urlpatterns as distance_api_urls
    except Exception:
        distance_api_urls = []

    urlpatterns += [
        path('api/auth/jwt/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/auth/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
        path('api/v1/', include(distance_api_urls)),
    ]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
