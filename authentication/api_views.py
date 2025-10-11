from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .permissions import IsOwnerOrAdmin, IsPatient
from .serializers import CustomUserSerializer, UserRegisterSerializer

User = get_user_model()


class AllowAnyRegisterPermission(permissions.AllowAny):
    pass


class IsAdminOrSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.id == request.user.id


class UserRegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Option: ne pas générer de tokens ici, simple confirmation
        return response


class UserViewSet(viewsets.ModelViewSet):
    """CRUD Users.

    Règles:
    - list/destroy : admin only (IsAdminUser)
    - retrieve/update/partial_update : owner ou admin
    - me (GET/PATCH) : utilisateur courant (géré directement)
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):  # pragma: no cover simple branching
        if self.action in ["list", "destroy"]:
            return [IsAdminUser()]
        if self.action in ["retrieve", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            # Un non-admin ne voit que lui-même
            qs = qs.filter(id=self.request.user.id)
        return qs

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        user = request.user
        if request.method == "GET":
            return Response(self.get_serializer(user).data)
        # PATCH partiel sur champs autorisés
        partial = True
        serializer = UserRegisterSerializer(user, data=request.data, partial=partial)
        allowed = {"first_name", "last_name", "email"}
        for field in list(serializer.initial_data.keys()):
            if field not in allowed:
                serializer.initial_data.pop(field)
        if serializer.is_valid():
            serializer.save()
            return Response(CustomUserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MedecinViewSet(viewsets.ReadOnlyModelViewSet):
    """Liste/lecture des médecins. Accès réservé aux patients authentifiés."""

    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="available", description="Filtrer les médecins disponibles (true/false)", required=False, type=str
            ),
            OpenApiParameter(name="specialty", description="Filtrer par spécialité", required=False, type=str),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):  # pragma: no cover - simple filter
        qs = User.objects.filter(role="medecin").select_related("medecin_profile").order_by("username")
        params = getattr(self.request, "query_params", {})
        available = params.get("available")
        specialty = params.get("specialty")
        if available in ("true", "True", "1"):
            qs = qs.filter(medecin_profile__is_available=True)
        if available in ("false", "False", "0"):
            qs = qs.filter(medecin_profile__is_available=False)
        if specialty:
            qs = qs.filter(medecin_profile__specialty__icontains=specialty)
        return qs

    @extend_schema(summary="Lister uniquement les médecins disponibles")
    @action(detail=False, methods=["get"], url_path="available")
    def available(self, request):
        qs = self.get_queryset().filter(medecin_profile__is_available=True)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)
