from rest_framework.permissions import BasePermission


class IsProfileOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsTeamOwner(BasePermission):
    """
    Custom permission to allow only the team owner to access the team.
    """

    def has_permission(self, request, view):
        return hasattr(request.user, "owned_team")
