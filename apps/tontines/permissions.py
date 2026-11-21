from rest_framework.permissions import BasePermission

from .models import Adhesion


class PermissionRoleTontine(BasePermission):
    message = "Acces refuse pour cette tontine ou ce role."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tontine_id = view.kwargs.get("tontine_id") or view.kwargs.get("pk")
        if tontine_id is None:
            return False

        role_requis = getattr(view, "role_requis", None)
        if role_requis is None:
            return True

        adhesion = Adhesion.objects.filter(utilisateur=request.user, tontine_id=tontine_id).first()
        if adhesion is None:
            return False
        return adhesion.role == role_requis

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        tontine = getattr(obj, "tontine", obj)
        role_requis = getattr(view, "role_requis", None)
        adhesion = Adhesion.objects.filter(utilisateur=request.user, tontine=tontine).first()
        if adhesion is None:
            return False
        if role_requis is None:
            return True
        return adhesion.role == role_requis
