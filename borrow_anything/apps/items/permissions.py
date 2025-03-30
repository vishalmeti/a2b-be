# apps/items/permissions.py

from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit/delete it.
    Read-only access is allowed for any authenticated request (GET, HEAD, OPTIONS).
    Assumes the model instance has an `owner_profile` attribute that links to UserProfile.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions (PUT, PATCH, DELETE) are only allowed if the
        # request.user has a profile and that profile is the owner of the item.
        # Use getattr for safer access in case request.user somehow doesn't have 'profile'.
        return obj.owner_profile == getattr(request.user, 'profile', None)