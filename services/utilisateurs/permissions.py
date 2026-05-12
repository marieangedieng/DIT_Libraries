from rest_framework.permissions import BasePermission
from .models import UtilisateurBibliotheque

class IsAdminUserCustom(BasePermission):
    """
    Permission : seuls les admins peuvent gérer les utilisateurs.
    Les autres rôles ont accès en lecture seule.
    """
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, "type_utilisateur"):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.type_utilisateur == UtilisateurBibliotheque.TypeUtilisateur.ADMIN
