# apps/items/admin.py

from django.contrib import admin
from django.utils.html import format_html  # Optional: For displaying images if possible
from django.conf import settings  # Optional: If needed to construct S3 URLs

from .models import Category, Item, ItemImage


# 1. Inline Admin for Item Images within the Item page
class ItemImageInline(
    admin.TabularInline
):  # Or use admin.StackedInline for different layout
    model = ItemImage
    fields = ("s3_key", "caption")  # Fields to show for each image inline
    extra = 1  # How many empty extra forms to show
    # If keys are managed ONLY via external uploads, make it read-only:
    # readonly_fields = ('s3_key',)
    verbose_name = "Item Image Reference"
    verbose_name_plural = "Item Image References (S3 Keys)"

    # Optional: Attempt to display thumbnail - requires manual URL construction
    # readonly_fields = ('image_thumbnail',)
    # def image_thumbnail(self, obj):
    #     if obj.s3_key:
    #         # WARNING: Assumes public bucket or requires complex pre-signing logic here
    #         # Construct the URL manually based on your bucket/settings
    #         # This is one reason ImageField + django-storages is easier
    #         bucket_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/"
    #         full_url = bucket_url + obj.s3_key
    #         return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', full_url)
    #     return "No S3 Key"
    # image_thumbnail.short_description = 'Thumbnail Preview (if public)'


# 2. Admin configuration for Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "id")  # Show ID for reference
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)


# 3. Admin configuration for Item
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner_profile_link",  # Use custom method for link
        "category",
        "community_link",  # Use custom method for link
        "availability_status",
        "is_active",
        "created_at",
    )
    list_filter = (
        "availability_status",
        "is_active",
        "category",
        "community",
        "condition",
    )
    search_fields = (
        "title",
        "description",
        "owner_profile__user__username",  # Search by owner's username
        "community__name",  # Search by community name
        "category__name",  # Search by category name
    )
    # Fields shown when editing/adding an Item
    fieldsets = (
        (None, {"fields": ("title", "description", "category")}),
        (
            "Ownership & Location",
            {
                # Make owner/community read-only as they should be set programmatically
                "fields": ("owner_profile", "community"),
            },
        ),
        (
            "Item Details & Terms",
            {
                "fields": (
                    "condition",
                    "availability_status",
                    "availability_notes",
                    "deposit_amount",
                    "borrowing_fee",
                    "max_borrow_duration_days",
                    "pickup_details",
                )
            },
        ),
        (
            "Status",
            {
                "fields": ("is_active", "average_item_rating"),
            },
        ),
    )
    # Make certain fields read-only in the detail view
    readonly_fields = (
        "owner_profile",
        "community",
        "average_item_rating",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    # Include the ItemImageInline editor on the Item page
    inlines = [ItemImageInline]

    # Custom methods to make owner/community links clickable
    @admin.display(description="Owner")
    def owner_profile_link(self, obj):
        from django.urls import reverse
        if obj.owner_profile:
            # Link to auth User instead of UserProfile
            link = reverse("admin:auth_user_change", args=[obj.owner_profile.user.id])
            return format_html(
                '<a href="{}">{}</a>', link, obj.owner_profile.user.username
            )
        return None

    @admin.display(description="Community")
    def community_link(self, obj):
        from django.urls import reverse

        if obj.community:
            link = reverse(
                "admin:communities_community_change", args=[obj.community.id]
            )
            return format_html('<a href="{}">{}</a>', link, obj.community.name)
        return None


# 4. Register ItemImage only if you want a separate top-level admin for it
# (Generally managing them via the Item inline is sufficient)
# @admin.register(ItemImage)
# class ItemImageAdmin(admin.ModelAdmin):
#     list_display = ('item', 's3_key', 'caption', 'uploaded_at')
#     search_fields = ('item__title', 's3_key', 'caption')
#     readonly_fields = ('image_thumbnail',) # Add thumbnail preview here too if using
