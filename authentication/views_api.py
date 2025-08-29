from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import CustomUserSerializer
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse


class EmptySerializer(serializers.Serializer):
    """Serializer neutre pour endpoints sans payload structuré."""
    pass


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer  # entrée (refresh string) non structurée -> doc minimal

    @extend_schema(
        request=EmptySerializer,
        responses={205: OpenApiResponse(response=EmptySerializer, description='Token invalidé')},
        summary="Déconnexion (blacklist refresh)",
        tags=['Auth']
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Missing refresh token'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Logged out'}, status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """Retourne le profil de l'utilisateur courant."""
    permission_classes = [IsAuthenticated]
    serializer_class = CustomUserSerializer

    @extend_schema(
        responses={200: CustomUserSerializer},
        summary="Profil utilisateur courant",
        tags=['Auth']
    )
    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)



