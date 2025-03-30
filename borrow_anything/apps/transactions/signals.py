# apps/transactions/signals.py

from django.db.models.signals import post_save # Signal sent after a model's save() is called
from django.dispatch import receiver # Decorator to connect a function to a signal
import logging # Use logging for messages

# Import models involved
from .models import BorrowingRequest, Review

# Get a logger instance for this module
logger = logging.getLogger(__name__)

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

# --- You can add other signal receivers for the transactions app below ---
# For example, functions to trigger Notifications on various status changes
# @receiver(post_save, sender=BorrowingRequest)
# def send_transaction_notifications(sender, instance, created, update_fields=None, **kwargs):
#     if created:
#         # Logic to create 'New Request' notification for lender
#         pass
#     elif not created and status_field_updated:
#         # Logic to check instance.status and create relevant notifications
#         # for borrower or lender (e.g., Accepted, Declined, Picked Up, Returned, Completed etc.)
#         pass