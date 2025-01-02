from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user and request.user.is_authenticated:
            if view.__class__.__name__ == "ProfileViewSet":
                return obj.user.profile == request.user.profile
            return obj.author == request.user.profile
        return False
