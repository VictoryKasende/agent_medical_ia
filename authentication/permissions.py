from rest_framework import permissions

class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'patient')

class IsMedecin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'medecin')

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))

class IsAdminOrMedecin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', None) == 'medecin'))

class IsOwnerOrAdmin(permissions.BasePermission):
    """Object-level permission: owner or admin."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return getattr(obj, 'id', None) == request.user.id or getattr(obj, 'user_id', None) == request.user.id
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'patient')


class IsMedecin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'medecin')


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrAdmin(BasePermission):
    """Object-level: owner (user fk) or staff."""
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsMedecin(BasePermission):
    message = "Accès réservé aux médecins." 
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'medecin')


class IsPatient(BasePermission):
    message = "Accès réservé aux patients." 
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'patient')


class IsMedecinOrAdmin(BasePermission):
    message = "Accès réservé aux médecins ou administrateurs." 
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (getattr(u, 'role', None) == 'medecin' or u.is_staff))


class IsOwnerOrMedecin(BasePermission):
    message = "Seul le propriétaire ou un médecin peut accéder à cette ressource." 
    def has_object_permission(self, request, view, obj):
        # Suppose futur lien fiche.user si ajouté; fallback accepte seulement médecins sinon
        if request.user.is_staff or getattr(request.user, 'role', None) == 'medecin':
            return True
        owner = getattr(obj, 'user', None)
        return owner == request.user

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsMedecin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'medecin')

class IsMedecinOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.is_superuser or getattr(request.user, 'role', None) == 'medecin'

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
<<<<<<< HEAD


class IsMedecinOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == 'medecin' or request.user.is_staff))
from rest_framework.permissions import BasePermission


class IsMedecin(BasePermission):
    message = "Accès réservé aux médecins."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'medecin')
=======
>>>>>>> api-docs-tests
