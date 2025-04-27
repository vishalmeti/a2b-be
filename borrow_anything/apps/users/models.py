# apps/users/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F, ExpressionWrapper, FloatField
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

    cover_photo_s3_key = models.CharField(
        max_length=1024,
        blank=True,
        null=True,  # Allow cover photo to be optional
        help_text="S3 object key for the cover photo",
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

    # Rating fields
    average_rating = models.FloatField(
        default=3.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Average rating received by the user (0-5)",
    )
    rating_count = models.PositiveIntegerField(
        default=0, help_text="Total number of ratings received"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Update the string representation to include community name again
        community_name = self.community.name if self.community else "No Community"
        return f"{self.user.username} ({community_name})"

    def update_rating(self, new_rating):
        """
        Updates the user's average rating based on a new rating received.
        Handles the calculation atomically to prevent race conditions.
        """
        if new_rating is None or not (1 <= new_rating <= 5):
            return # Do nothing if the rating is invalid

        # Use F expressions for atomic update
        UserProfile.objects.filter(pk=self.pk).update(
            average_rating=(
                (F('average_rating') * F('rating_count')) + new_rating
            ) / (F('rating_count') + 1),
            rating_count=F('rating_count') + 1
        )
        # Refresh the instance data from the database
        self.refresh_from_db(fields=['average_rating', 'rating_count'])


class UserCommunityMembership(models.Model):
    """
    Tracks membership of users across multiple communities.
    A user can join multiple communities and this model records those relationships.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_memberships"
    )
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,
        related_name="user_memberships"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Is user's membership in this community verified (e.g., via RWA check)?"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the user's primary community? Only one community can be primary."
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'community']
        verbose_name_plural = "User Community Memberships"
    
    def __str__(self):
        return f"{self.user.username} in {self.community.name}"
    
    def save(self, *args, **kwargs):
        # If this membership is being set as primary, unset any other primary memberships
        if self.is_primary:
            # Get all other memberships for this user
            UserCommunityMembership.objects.filter(
                user=self.user, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
            
            # Also update the user's profile to make this their primary community
            profile, created = UserProfile.objects.get_or_create(user=self.user)
            profile.community = self.community
            profile.save(update_fields=['community'])
            
        super().save(*args, **kwargs)
