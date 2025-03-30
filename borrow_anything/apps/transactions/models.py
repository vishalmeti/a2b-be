# apps/transactions/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone  # For setting timestamps on actions

# Import related models from other apps
from apps.items.models import Item
from apps.users.models import UserProfile


class BorrowingRequest(models.Model):
    """
    Represents a request from a borrower to a lender for an item,
    and tracks the lifecycle of the borrowing transaction.
    """

    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Pending Lender Approval"  # Initial state
        ACCEPTED = (
            "ACCEPTED",
            "Accepted by Lender",
        )  # Lender agrees, ready for pickup coordination
        DECLINED = "DECLINED", "Declined by Lender"  # Lender rejects
        CANCELLED_BORROWER = (
            "CANCELLED_BORROWER",
            "Cancelled by Borrower",
        )  # Borrower cancels before pickup
        CANCELLED_LENDER = (
            "CANCELLED_LENDER",
            "Cancelled by Lender",
        )  # Lender cancels after accepting, before pickup
        PICKED_UP = (
            "PICKED_UP",
            "Item Picked Up",
        )  # Borrower confirms they have the item
        RETURNED = (
            "RETURNED",
            "Item Returned by Borrower",
        )  # Borrower confirms they returned, pending lender confirmation
        COMPLETED = (
            "COMPLETED",
            "Completed",
        )  # Lender confirms item returned okay. Ready for review.
        # Future: OVERDUE, DISPUTED?

    # Core relationships
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,  # Don't delete item if active requests exist
        related_name="requests",
        help_text="The item being requested for borrowing",
    )
    borrower_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,  # Don't delete user if active requests exist
        related_name="borrow_requests",
        help_text="The user profile of the person requesting the item",
    )
    # Denormalized for easier querying/access, set automatically in save()
    lender_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        related_name="lend_requests",
        help_text="The user profile of the item owner (lender)",
    )

    # Requested timeframe
    start_date = models.DateField(
        db_index=True, help_text="Requested borrow start date"
    )
    end_date = models.DateField(db_index=True, help_text="Requested borrow end date")

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        db_index=True,
        help_text="The current status of the borrowing request",
    )

    # Communication artifacts (optional messages during state changes)
    borrower_message = models.TextField(
        blank=True, help_text="Optional message from borrower with the initial request"
    )
    lender_response_message = models.TextField(
        blank=True, help_text="Optional message from lender when accepting/declining"
    )

    # Timestamps for key actions in the lifecycle
    # Action timestamps should be set when the corresponding status change occurs
    created_at = models.DateTimeField(auto_now_add=True)  # When request was made
    updated_at = models.DateTimeField(auto_now=True)  # Last modification time
    processed_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when lender Accepted or Declined"
    )
    pickup_confirmed_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when borrower confirmed pickup"
    )
    return_initiated_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when borrower marked as returned"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when lender confirmed return (transaction completed)",
    )

    def save(self, *args, **kwargs):
        # Automatically set the lender based on the item's owner
        if self.item:
            self.lender_profile = self.item.owner_profile
        # Add logic here or via signals to update Item.availability_status based on self.status changes
        # e.g., if status becomes PICKED_UP, set item.availability_status = BORROWED
        # e.g., if status becomes COMPLETED/CANCELLED_*, set item.availability_status = AVAILABLE (if no other requests)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Request for '{self.item.title}' by {self.borrower_profile.user.username} ({self.get_status_display()})"

    class Meta:
        ordering = ["-created_at"]
        # Consider constraints, e.g., prevent overlapping requests for the same item? (Can be complex)


class Review(models.Model):
    """
    Stores ratings and comments left by users after a borrowing transaction is completed.
    Should ideally be created when a BorrowingRequest status becomes COMPLETED.
    """

    # Link securely to the completed transaction
    borrowing_request = models.OneToOneField(
        BorrowingRequest,
        on_delete=models.CASCADE,  # If the request is deleted, delete the review
        related_name="review",  # Access review via request.review
        help_text="The completed borrowing request being reviewed",
    )

    # --- Feedback from Borrower (about Lender) ---
    rating_for_lender = models.PositiveSmallIntegerField(
        null=True,
        blank=True,  # Allow submitting only comment or only rating
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Borrower's rating of the lender (1-5 Stars)",
    )
    comment_for_lender = models.TextField(
        blank=True,
        help_text="Borrower's comments about their interaction with the lender",
    )
    borrower_review_submitted_at = models.DateTimeField(null=True, blank=True)

    # --- Feedback from Lender (about Borrower & Item Condition) ---
    rating_for_borrower = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Lender's rating of the borrower (1-5 Stars)",
    )
    comment_for_borrower = models.TextField(
        blank=True,
        help_text="Lender's comments about their interaction with the borrower",
    )
    # Rating by lender on the item's condition when returned
    rating_for_item_condition_on_return = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Lender's rating of the item's condition upon return (1-5 Stars)",
    )
    comment_on_item_condition = models.TextField(
        blank=True,
        help_text="Lender's comments about the item's condition when returned",
    )
    lender_review_submitted_at = models.DateTimeField(null=True, blank=True)

    # Timestamps for the review itself
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review for Request ID: {self.borrowing_request.id} (Item: {self.borrowing_request.item.title})"

    class Meta:
        ordering = ["-created_at"]
        # Ensure only one review record per borrowing request (handled by OneToOneField)
