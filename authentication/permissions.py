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


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
