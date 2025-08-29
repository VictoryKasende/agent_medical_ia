from django.urls import path, includefrom django.urls import path

from rest_framework.routers import DefaultRouterfrom rest_framework_simplejwt.views import (

from .api_views import UserRegisterAPIView, UserViewSet    TokenObtainPairView,

    TokenRefreshView,

router = DefaultRouter()    TokenVerifyView,

router.register('users', UserViewSet, basename='user'))

from .views_api import LogoutView, MeView

urlpatterns = [

    path('users/register/', UserRegisterAPIView.as_view(), name='user-register'),app_name = 'auth_api'

    path('', include(router.urls)),

]urlpatterns = [

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
]


