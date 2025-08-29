from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from django.contrib.auth import get_user_model
from .serializers import CustomUserSerializer, UserRegisterSerializer
from .permissions import IsAdmin, IsOwnerOrAdmin

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
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'destroy']:
            return [IsAdmin()]
        if self.action in ['retrieve', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            # Un non-admin ne voit que lui-même
            qs = qs.filter(id=self.request.user.id)
        return qs

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            return Response(self.get_serializer(user).data)
        # PATCH partiel sur champs autorisés
        partial = True
        serializer = UserRegisterSerializer(user, data=request.data, partial=partial)
        allowed = {'first_name', 'last_name', 'email'}
        for field in list(serializer.initial_data.keys()):
            if field not in allowed:
                serializer.initial_data.pop(field)
        if serializer.is_valid():
            serializer.save()
            return Response(CustomUserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
