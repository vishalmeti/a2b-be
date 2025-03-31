# apps/notifications/permissions.py

from rest_framework import permissions

class IsNotificationRecipient(permissions.BasePermission):
    """
    Object-level permission to only allow the recipient of a notification
    to view or modify it.
    """
    message = "You do not have permission to access this notification."

    def has_object_permission(self, request, view, obj):
        """
        Check if the request.user's profile matches the notification's recipient.
        Assumes 'obj' is the Notification instance.
        """
        # Get the user profile associated with the incoming request user
        user_profile = getattr(request.user, 'profile', None)

        # Check if the user has a profile and if it matches the notification's recipient
        # Also ensure the notification object has a recipient set.
        return user_profile and hasattr(obj, 'recipient') and obj.recipient == user_profile
