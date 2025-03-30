# apps/users/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.communities.models import Community

# Note: We are NOT importing Community model yet


class UserProfile(models.Model):
    """
    Extends the built-in User model with app-specific details.
    Community link will be added in a later migration.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="profile",
    )

    community = models.ForeignKey(
        Community,  # Reference the imported Community model
        on_delete=models.SET_NULL,  # If a community is deleted, set this field to NULL
        null=True,
        blank=True,  # Allows profiles to exist without a community (important for existing rows & optionality)
        related_name="residents",  # Allows community.residents.all() lookup
        help_text="The primary community this user belongs to",
    )

    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    address_details = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional: e.g., Flat No, Block - use minimally for privacy",
    )
    profile_picture_s3_key = models.CharField(
        max_length=1024,
        blank=True,
        null=True,  # Allow profile picture to be optional
        help_text="S3 object key for the profile picture",
    )

    is_community_member_verified = models.BooleanField(
        default=False,
        help_text="Is user's membership in their selected community verified (e.g., via RWA check)?",
        # This field's meaning is limited until the community link exists
    )

    average_lender_rating = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
    )
    average_borrower_rating = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Update the string representation to include community name again
        community_name = self.community.name if self.community else "No Community"
        return f"{self.user.username} ({community_name})"


# Optional: Signal handler can still be added here or later
# It won't affect the community field yet.
