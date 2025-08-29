from rest_framework.permissions import BasePermission


class IsMedecin(BasePermission):
    message = "Accès réservé aux médecins."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'medecin')
