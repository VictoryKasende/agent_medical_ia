"""Centralisation des permissions custom pour l'API.

Nettoyage post-refonte: suppression de nombreuses duplications issues de merges.
Seules les classes nécessaires sont conservées avec messages explicites.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS



class IsAuthenticatedAndRole(BasePermission):
    required_role: str | None = None
    message = "Rôle requis."

    def has_permission(self, request, view):  # pragma: no cover (simple)
        if not (request.user and request.user.is_authenticated):
            return False
        if self.required_role is None:
            return True
        return getattr(request.user, 'role', None) == self.required_role


class IsPatient(IsAuthenticatedAndRole):
    required_role = 'patient'
    message = "Accès réservé aux patients."


class IsMedecin(IsAuthenticatedAndRole):
    required_role = 'medecin'
    message = "Accès réservé aux médecins."


class IsMedecinOrAdmin(BasePermission):
    message = "Accès réservé aux médecins ou administrateurs."

    def has_permission(self, request, view):  # pragma: no cover (simple)
        u = request.user
        return bool(u and u.is_authenticated and (getattr(u, 'role', None) == 'medecin' or u.is_staff))


class IsOwnerOrAdmin(BasePermission):
    """Permission objet: propriétaire (user fk) ou staff/superuser."""
    message = "Accès réservé au propriétaire ou administrateur."

    def has_object_permission(self, request, view, obj):  # pragma: no cover (simple)
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff or getattr(request.user, 'is_superuser', False):
            return True
        owner = getattr(obj, 'user', None)
        if owner is not None:
            return owner == request.user
        # fallback id/user_id
        return getattr(obj, 'user_id', None) == request.user.id or getattr(obj, 'id', None) == request.user.id


class ReadOnly(BasePermission):
    def has_permission(self, request, view):  # pragma: no cover (simple)
        return request.method in SAFE_METHODS


__all__ = [
    'IsPatient', 'IsMedecin', 'IsMedecinOrAdmin', 'IsOwnerOrAdmin', 'ReadOnly'
]
