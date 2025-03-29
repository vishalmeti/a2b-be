from django.db import models
from django.conf import settings  # Use settings.AUTH_USER_MODEL


class Community(models.Model):
    """
    Represents an approved, distinct hyperlocal area (e.g., apartment complex, layout).
    Records are typically created by Admins or via approval of CommunitySuggestions.
    """

    name = models.CharField(
        max_length=200,
        help_text="Official or commonly known name (e.g., Prestige Shantiniketan)",
    )
    city = models.CharField(max_length=100, db_index=True)
    pincode = models.CharField(max_length=10, db_index=True)
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Approximate center latitude",
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Approximate center longitude",
    )
    # Controls visibility and joinability
    is_approved = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Has this community been approved by admin?",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Is this community currently active/visble?",
    )
    is_officially_verified = models.BooleanField(
        default=False,
        help_text="Represents formal verification/partnership with management/RWA",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Communities"
        # Ensure combination of name, city, pincode is unique to avoid exact duplicates
        unique_together = [["name", "city", "pincode"]]
        ordering = ["city", "name"]

    def __str__(self):
        return f"{self.name}, {self.city} ({self.pincode})"


class CommunitySuggestion(models.Model):
    """
    Stores user suggestions for new communities pending admin review.
    """

    class SuggestionStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        APPROVED = "APPROVED", "Approved (Community Created)"
        REJECTED_DUPLICATE = "REJECTED_DUPLICATE", "Rejected - Duplicate"
        REJECTED_INVALID = "REJECTED_INVALID", "Rejected - Invalid/Spam"
        MERGED = "MERGED", "Merged with Existing"

    suggested_name = models.CharField(
        max_length=200, help_text="Name suggested by the user"
    )
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    suggested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Keep suggestion even if user deleted
        null=True,
        related_name="community_suggestions",
    )
    status = models.CharField(
        max_length=20,
        choices=SuggestionStatus.choices,
        default=SuggestionStatus.PENDING,
        db_index=True,
    )
    admin_notes = models.TextField(
        blank=True, help_text="Notes from admin during review"
    )
    # Link to the created community if approved
    created_community = models.OneToOneField(
        Community,
        on_delete=models.SET_NULL,  # Don't delete suggestion if community deleted, just unlink
        null=True,
        blank=True,
        related_name="suggestion_source",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(
        null=True, blank=True
    )  # Timestamp of admin action

    class Meta:
        ordering = ["status", "-created_at"]

    def __str__(self):
        # Check if suggested_by exists before accessing username
        suggester = self.suggested_by.username if self.suggested_by else "Unknown User"
        return f"Suggestion: '{self.suggested_name}' ({self.pincode}) by {suggester} - {self.get_status_display()}"
