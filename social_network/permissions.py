from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Checks if the current user has permission to perform an action
        on the object.

        Allows read-only access for safe methods. For authenticated users, 
        checks if the user is the owner of the object. Ownership is validated 
        differently based on the view class:
    
        - For ProfileViewSet, verifies if the profile associated with
        the object matches the requesting user's profile.
        - For other viewsets, compares the object's author with the requesting 
        user's profile.

        :param request: The current request object.
        :param view: The view handling the request.
        :param obj: The object to check permissions against.
        :return: True if the user has permission, False otherwise.
        """

        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user and request.user.is_authenticated:
            if view.__class__.__name__ == "ProfileViewSet":
                return obj.user.profile == request.user.profile
            return obj.author == request.user.profile
        return False
