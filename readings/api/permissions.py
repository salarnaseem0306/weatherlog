from rest_framework import permissions


class IsOwnerOrStaffOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not (request.user and request.user.is_authenticated):
            return False  
        if request.user.is_staff:
            return True
        return getattr(view, "owner_field", None) is not None

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        owner_field = getattr(view, "owner_field", None)
        if owner_field is None:
            return False
        return getattr(obj, f"{owner_field}_id", None) == request.user.id