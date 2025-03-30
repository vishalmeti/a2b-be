# apps/notifications/models.py

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _  # For choices text

# Import related models - use settings.AUTH_USER_MODEL indirectly via UserProfile
from apps.users.models import UserProfile

# Use string paths to avoid potential circular imports if models grow complex
# from apps.transactions.models import BorrowingRequest
# from apps.items.models import Item


class Notification(models.Model):
    """
    Represents a notification sent to a user regarding an event.
    """

    # Define choices for the type of notification
    class NotificationTypeChoices(models.TextChoices):
        # Borrowing Request Lifecycle
        REQUEST_RECEIVED = "REQ_REC", _("New Borrow Request Received")
        REQUEST_ACCEPTED = "REQ_ACC", _("Request Accepted")
        REQUEST_DECLINED = "REQ_DEC", _("Request Declined")
        REQUEST_CANCELLED_BORROWER = "REQ_CAN_BOR", _("Request Cancelled by Borrower")
        REQUEST_CANCELLED_LENDER = "REQ_CAN_LEN", _(
            "Request Cancelled by Lender"
        )  # Need action for this later
        PICKUP_CONFIRMED = "PICKUP_CONF", _("Item Pickup Confirmed")
        RETURN_CONFIRMED_BORROWER = "RET_CONF_BOR", _("Item Return Initiated")
        REQUEST_COMPLETED = "REQ_COMP", _("Borrowing Completed")
        # Reviews
        REVIEW_RECEIVED = "REV_REC", _("New Review Received")
        REVIEW_PROMPT = "REV_PROMPT", _("Reminder to Leave Review")
        # Community
        COMMUNITY_SUGGESTION_APPROVED = "COM_SUG_APP", _(
            "Community Suggestion Approved"
        )
        COMMUNITY_SUGGESTION_REJECTED = "COM_SUG_REJ", _(
            "Community Suggestion Rejected"
        )
        # Messaging (Planned)
        NEW_MESSAGE = "NEW_MSG", _("New Message Received")
        # General / Admin
        GENERAL_INFO = "GEN_INFO", _("Information")

    # --- Core Fields ---
    recipient = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,  # If user profile deleted, delete their notifications
        related_name="notifications",
        help_text="The user profile receiving the notification.",
    )
    # Optional: The user who triggered the notification
    actor = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,  # Keep notification even if actor deleted
        null=True,
        blank=True,
        related_name="triggered_notifications",
        help_text="The user profile who performed the action causing the notification (optional).",
    )
    message = models.TextField(help_text="The main content/text of the notification.")
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationTypeChoices.choices,
        db_index=True,
        help_text="Categorizes the notification for display or handling.",
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Has the recipient marked this notification as read?",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, db_index=True, help_text="When the notification was created."
    )

    # --- Optional Links to Related Objects ---
    # Use string paths 'app_name.ModelName' to avoid circular imports
    related_request = models.ForeignKey(
        "transactions.BorrowingRequest",
        on_delete=models.SET_NULL,  # Keep notification even if request deleted
        null=True,
        blank=True,
        related_name="+",  # No reverse relation needed from request back to notification
        help_text="Link to the relevant Borrowing Request, if applicable.",
    )
    related_item = models.ForeignKey(
        "items.Item",
        on_delete=models.SET_NULL,  # Keep notification even if item deleted
        null=True,
        blank=True,
        related_name="+",  # No reverse relation needed
        help_text="Link to the relevant Item, if applicable.",
    )
    # Optional link back to a user profile (e.g., if notification is "User X reviewed you")
    # Avoids overloading the 'actor' field if the context is different
    related_user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",  # No reverse relation needed
        help_text="Link to another User Profile relevant to the notification (optional).",
    )
    # Add FK for related Review if needed:
    # related_review = models.ForeignKey('transactions.Review', ...)

    class Meta:
        ordering = ["-created_at"]  # Show newest first by default
        indexes = [
            models.Index(
                fields=["recipient", "is_read", "-created_at"]
            ),  # Index for fetching user's unread notifications
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        read_status = "Read" if self.is_read else "Unread"
        return f"To: {self.recipient.user.username} - Type: {self.get_notification_type_display()} ({read_status})"
