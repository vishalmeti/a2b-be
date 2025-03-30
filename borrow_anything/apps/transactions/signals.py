# apps/transactions/signals.py

from django.db.models.signals import post_save # Signal sent after a model's save() is called
from django.dispatch import receiver # Decorator to connect a function to a signal
import logging # Use logging for messages

# Import models involved
from .models import BorrowingRequest, Review

# Get a logger instance for this module
logger = logging.getLogger(__name__)

from apps.notifications.models import Notification

# Import UserProfile to link actor/recipient correctly
from apps.users.models import UserProfile


# Decorator connects this function to the post_save signal for the BorrowingRequest model
@receiver(post_save, sender=BorrowingRequest)
def create_review_on_request_completion(sender, instance, created, update_fields=None, **kwargs):
    """
    Signal receiver that automatically creates a Review object when a
    BorrowingRequest instance is saved with status='COMPLETED'.
    """
    # We only care about updates, not when a request is first created
    if not created:
        # Check if the 'status' field was part of the update, or if we don't know which fields were updated
        status_field_updated = update_fields is None or 'status' in update_fields

        # Check if the new status is COMPLETED
        if status_field_updated and instance.status == BorrowingRequest.StatusChoices.COMPLETED:
            # Use get_or_create:
            # - Tries to get a Review linked to this borrowing_request.
            # - If it doesn't exist, it creates one.
            # - This prevents errors if the signal somehow runs twice or if a review was manually created.
            review, review_created = Review.objects.get_or_create(
                borrowing_request=instance # The OneToOneField links directly to the instance
            )

            if review_created:
                logger.info(f"Review record automatically created for completed BorrowingRequest ID: {instance.pk}")
                # You could potentially trigger an initial "Please leave a review" notification here too
            # else:
            # logger.info(f"Review record already existed for BorrowingRequest ID: {instance.pk}")


# --- Signal Receiver for BorrowingRequest Status Changes ---


@receiver(post_save, sender=BorrowingRequest)
def handle_request_status_change(
    sender, instance: BorrowingRequest, created, update_fields=None, **kwargs
):
    """
    Listens for saves on BorrowingRequest and creates Notifications
    for relevant status changes or creation.
    """
    recipient: UserProfile | None = None
    actor: UserProfile | None = None
    message: str = ""
    notification_type: Notification.NotificationTypeChoices | None = None
    related_item = instance.item  # Get the item once

    # Determine if status was actually updated if update_fields is available
    status_updated = update_fields is None or "status" in update_fields

    # --- Event: New Request Created ---
    if created:
        recipient = instance.lender_profile
        actor = instance.borrower_profile
        notification_type = Notification.NotificationTypeChoices.REQUEST_RECEIVED
        message = (
            f"{actor.user.username} requested to borrow your item: {related_item.title}"
        )

    # --- Event: Status Updated (Not Creation) ---
    elif status_updated:
        current_status = instance.status
        actor = None  # Actor determined by who likely triggered the change

        # Lender Actions -> Notify Borrower
        if current_status == BorrowingRequest.StatusChoices.ACCEPTED:
            recipient = instance.borrower_profile
            actor = instance.lender_profile  # Lender accepted
            notification_type = Notification.NotificationTypeChoices.REQUEST_ACCEPTED
            message = f"Your request for '{related_item.title}' was accepted by {actor.user.username}."
        elif current_status == BorrowingRequest.StatusChoices.DECLINED:
            recipient = instance.borrower_profile
            actor = instance.lender_profile  # Lender declined
            notification_type = Notification.NotificationTypeChoices.REQUEST_DECLINED
            message = f"Your request for '{related_item.title}' was declined by {actor.user.username}."
            if instance.lender_response_message:
                message += f" Reason: {instance.lender_response_message}"
        elif current_status == BorrowingRequest.StatusChoices.COMPLETED:
            recipient = instance.borrower_profile
            actor = instance.lender_profile  # Lender completed
            notification_type = (
                Notification.NotificationTypeChoices.REQUEST_COMPLETED
            )  # Or REVIEW_PROMPT?
            message = f"Your borrowing of '{related_item.title}' is complete. Please leave a review for {actor.user.username}!"
            # TODO: Could potentially create a separate REVIEW_PROMPT notification too

        # Borrower Actions -> Notify Lender
        elif current_status == BorrowingRequest.StatusChoices.CANCELLED_BORROWER:
            recipient = instance.lender_profile
            actor = instance.borrower_profile  # Borrower cancelled
            notification_type = (
                Notification.NotificationTypeChoices.REQUEST_CANCELLED_BORROWER
            )
            message = f"{actor.user.username} cancelled their request for your item: {related_item.title}"
        elif current_status == BorrowingRequest.StatusChoices.PICKED_UP:
            recipient = instance.lender_profile
            actor = instance.borrower_profile  # Borrower confirmed pickup
            notification_type = Notification.NotificationTypeChoices.PICKUP_CONFIRMED
            message = f"{actor.user.username} confirmed pickup for your item: {related_item.title}"
        elif current_status == BorrowingRequest.StatusChoices.RETURNED:
            recipient = instance.lender_profile
            actor = instance.borrower_profile  # Borrower confirmed return
            notification_type = (
                Notification.NotificationTypeChoices.RETURN_CONFIRMED_BORROWER
            )
            message = f"{actor.user.username} marked '{related_item.title}' as returned. Please confirm receipt."

    # --- Create Notification if relevant event occurred ---
    if recipient and notification_type and message:
        try:
            Notification.objects.create(
                recipient=recipient,
                actor=actor,
                message=message,
                notification_type=notification_type,
                related_request=instance,
                related_item=related_item,
                # related_user_profile could be actor or recipient depending on context if needed
            )
            logger.info(
                f"Notification '{notification_type}' created for user {recipient.user_id} regarding request {instance.pk}"
            )
        except Exception as e:
            logger.error(
                f"Failed to create notification for request {instance.pk}: {e}"
            )


# --- Signal Receiver for Review Submissions ---


@receiver(post_save, sender=Review)
def handle_review_submission(
    sender, instance: Review, created, update_fields=None, **kwargs
):
    """
    Listens for saves on Review and creates Notifications when a user submits
    their part of the review.
    """
    # We only care about updates where a submission timestamp was set
    if not created:
        borrowing_request = instance.borrowing_request
        recipient: UserProfile | None = None
        actor: UserProfile | None = None
        message: str = ""
        notification_type: Notification.NotificationTypeChoices = (
            Notification.NotificationTypeChoices.REVIEW_RECEIVED
        )

        # Check if borrower review timestamp was just updated
        borrower_submitted = (
            update_fields is None or "borrower_review_submitted_at" in update_fields
        )
        if borrower_submitted and instance.borrower_review_submitted_at is not None:
            # Check if this is the *first* time it's being set (might need pre_save state or check against old value)
            # Simple approach: Notify on any save that includes the timestamp update
            recipient = borrowing_request.lender_profile
            actor = borrowing_request.borrower_profile
            message = f"{actor.user.username} left a review for your transaction regarding '{borrowing_request.item.title}'."

        # Check if lender review timestamp was just updated (use elif to avoid double notification on same save)
        elif update_fields is None or "lender_review_submitted_at" in update_fields:
            if instance.lender_review_submitted_at is not None:
                recipient = borrowing_request.borrower_profile
                actor = borrowing_request.lender_profile
                message = f"{actor.user.username} left a review for your transaction regarding '{borrowing_request.item.title}'."

        # Create Notification if relevant event occurred
        if recipient and actor and message:
            try:
                Notification.objects.create(
                    recipient=recipient,
                    actor=actor,
                    message=message,
                    notification_type=notification_type,
                    related_request=borrowing_request,
                    related_item=borrowing_request.item,
                    # related_review=instance # Add if you have related_review FK on Notification model
                )
                logger.info(
                    f"Notification '{notification_type}' created for user {recipient.user_id} regarding review for request {borrowing_request.pk}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to create review notification for request {borrowing_request.pk}: {e}"
                )
