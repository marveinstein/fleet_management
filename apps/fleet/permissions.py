from rest_framework import permissions


class IsAdminUserRole(permissions.BasePermission):
    """
    Allows access only to Admin role or Django superusers.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        profile = getattr(request.user, "profile", None)
        return bool(profile and profile.role == "admin")


class IsFleetManagerOrAdmin(permissions.BasePermission):
    """
    Allows access to Fleet Managers and Administrators.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        profile = getattr(request.user, "profile", None)
        return bool(profile and profile.role in ["admin", "manager"])


class IsDriverOwnerOrManager(permissions.BasePermission):
    """
    Individual Drivers can only read or create their own trips/fuel logs.
    Managers and Administrators have full access.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        profile = getattr(request.user, "profile", None)
        if not profile:
            return False
        if profile.role in ["admin", "manager"]:
            return True
        # For driver role:
        if profile.role == "driver" and profile.driver_profile:
            if hasattr(obj, "driver"):
                return obj.driver == profile.driver_profile
            if hasattr(obj, "driver_profile"):
                return obj.driver_profile == profile.driver_profile
        return False
