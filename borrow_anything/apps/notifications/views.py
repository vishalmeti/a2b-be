# apps/notifications/views.py

from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

# Import local models, serializers, and permissions
from .models import Notification
from .serializers import NotificationSerializer
from .permissions import IsNotificationRecipient


class NotificationViewSet(
    mixins.ListModelMixin,  # For GET /notifications/
    mixins.UpdateModelMixin,  # For PATCH /notifications/{pk}/ (to update is_read)
    mixins.DestroyModelMixin,  # For DELETE /notifications/{pk}/
    viewsets.GenericViewSet,
):  # Base class
    """
    ViewSet for viewing, managing, and deleting Notifications.
    - List: Shows notifications for the logged-in user.
    - Partial Update (PATCH): Used to mark a notification as read.
    - Destroy: Allows users to delete their notifications.
    - Mark All Read: Custom action to mark all unread notifications as read.
    """

    serializer_class = NotificationSerializer
    # Apply base authentication and ensure user is the recipient for detail views
    permission_classes = [permissions.IsAuthenticated, IsNotificationRecipient]

    def get_queryset(self):
        """
        This view should only return notifications for the currently authenticated user.
        """
        user_profile = getattr(self.request.user, "profile", None)
        if not user_profile:
            return Notification.objects.none()  # Return empty if no profile

        queryset = Notification.objects.filter(recipient=user_profile)

        # Optional filtering by read status: /notifications/?is_read=false
        is_read_filter = self.request.query_params.get("is_read")
        if is_read_filter is not None:
            is_read_value = is_read_filter.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(is_read=is_read_value)

        return queryset.order_by("-created_at")  # Show newest first

    # Note on Update (PATCH):
    # The UpdateModelMixin provides the partial_update method for PATCH requests.
    # Because our NotificationSerializer only marks 'is_read' as writable (not read-only),
    # sending a PATCH request to /notifications/{id}/ with body {"is_read": true}
    # will automatically work via the mixin to update only that field.
    # The IsNotificationRecipient permission ensures only the owner can do this.

    # Note on Destroy (DELETE):
    # The DestroyModelMixin provides the destroy method for DELETE requests.
    # The IsNotificationRecipient permission ensures only the owner can delete.

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request, *args, **kwargs):
        """
        Custom action to mark all unread notifications for the user as read.
        Accessed via POST /notifications/mark-all-read/
        """
        user_profile = getattr(request.user, "profile", None)
        if not user_profile:
            # Should be caught by IsAuthenticated, but double-check
            return Response(
                {"detail": "User profile not found."}, status=status.HTTP_403_FORBIDDEN
            )

        # Update notifications for the recipient where is_read is False
        updated_count = Notification.objects.filter(
            recipient=user_profile, is_read=False
        ).update(
            is_read=True
        )  # Perform bulk update

        return Response(
            {"detail": f"Marked {updated_count} notifications as read."},
            status=status.HTTP_200_OK,
        )
