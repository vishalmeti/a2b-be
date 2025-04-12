# apps/items/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError  # Import for custom validation

# Import related models from other apps
from apps.users.models import UserProfile
from apps.communities.models import Community


class Category(models.Model):
    """
    Categories for items (e.g., Kitchen, Travel, Electronics, Baby Gear).
    Managed by Admins.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Optional icon class (e.g., Font Awesome)",
    )
    is_active = models.BooleanField(
        default=True, help_text="Controls visibility of the category"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Item(models.Model):
    """
    Represents an item listed by a user for borrowing within their community.
    """

    # Choices for condition field
    class ItemCondition(models.TextChoices):
        NEW = "NEW", "New"
        LIKE_NEW = "LIKE_NEW", "Like New"
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair"
        POOR = "POOR", "Poor"

    # Choices for availability status field
    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        BOOKED = (
            "BOOKED",
            "Currently Booked",
        )  # Should be managed via Transactions logic
        # This status is set when a borrowing request is accepted
        BORROWED = (
            "BORROWED",
            "Currently Borrowed",
        )  # Should be managed via Transactions logic
        UNAVAILABLE = "UNAVAILABLE", "Temporarily Unavailable"  # Lender manually sets

    # Foreign Key to the UserProfile of the owner
    owner_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,  # If owner profile deleted, delete their items too
        related_name="owned_items",
    )
    # Denormalized from owner_profile for efficient filtering by community
    # Enforced via the clean method and requires owner to have a community set.
    community = models.ForeignKey(
        Community,
        on_delete=models.CASCADE,  # If community deleted, delete items within it
        related_name="community_items",
        # Removed null=True, blank=False - will enforce via clean()
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    # Foreign Key to the Category
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,  # Prevent deleting category if items are linked
        related_name="items",
    )
    condition = models.CharField(
        max_length=10, choices=ItemCondition.choices, default=ItemCondition.GOOD
    )
    availability_status = models.CharField(
        max_length=15,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.AVAILABLE,
        db_index=True,
    )
    availability_notes = models.TextField(
        blank=True, help_text="e.g., 'Weekends only', 'Msg me before requesting'"
    )
    # Optional Financials
    deposit_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.0)],
    )
    borrowing_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.0)],
    )
    # Borrowing Terms
    max_borrow_duration_days = models.PositiveIntegerField(
        null=True, blank=True, help_text="Max days per borrow (optional)"
    )
    pickup_details = models.TextField(
        blank=True, help_text="Default pickup instructions (e.g., 'Lobby pickup')"
    )
    # Management
    is_active = models.BooleanField(
        default=True, help_text="Set to False to hide/soft-delete", db_index=True
    )
    # Optional calculated field
    average_item_rating = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Custom validation run before saving (e.g., in Django Admin or ModelForms).
        """
        super().clean()  # Call parent clean method first
        
        # Remove automatic community assignment and require it to be explicitly set
        if not self.community:
            raise ValidationError("Community must be specified when creating an item.")

    def save(self, *args, **kwargs):
        # Remove automatic community assignment from owner's profile
        # The community should now be provided in the request data
        
        # Optionally, you can add logic to set availability_status based on conditions
        # For example, if the item is not active, set it to UNAVAILABLE
        if not self.is_active:
            self.availability_status = self.AvailabilityStatus.UNAVAILABLE
        
        if self.is_active and self.availability_status == self.AvailabilityStatus.UNAVAILABLE:
            self.availability_status = self.AvailabilityStatus.AVAILABLE

        # Add logic later to ensure availability_status reflects actual borrowing status
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (Owner: {self.owner_profile.user.username})"

    class Meta:
        ordering = ["-created_at"]


class ItemImage(models.Model):
    """Stores multiple images for an item."""

    # Foreign Key to the Item this image belongs to
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,  # If item deleted, delete its images
        related_name="images",  # Allows access like item.images.all()
    )
    # ImageField requires Pillow library: pip install Pillow
    s3_key = models.CharField(
        max_length=1024,  # S3 keys can be long
        blank=False,
        null=False,  # An ItemImage must have an associated key
        help_text="S3 object key for the item image",
    )
    caption = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        # Provides a useful representation, e.g., in admin
        return f"Image for {self.item.title} (ID: {self.item.id})"
