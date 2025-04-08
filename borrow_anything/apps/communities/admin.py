# apps/communities/admin.py

from django.utils import timezone
from django.contrib import admin, messages  # Import messages for feedback
from django.utils.translation import ngettext  # For pluralization in messages
from .models import Community, CommunitySuggestion


@admin.register(Community)  # Use decorator for registration
class CommunityAdmin(admin.ModelAdmin):
    # Customize how Communities are displayed in the list view
    list_display = (
        "name",
        "city",
        "pincode",
        "description",
        "is_approved",
        "is_active",
        "is_officially_verified",
        "created_at",
    )
    # Add filters to the sidebar
    list_filter = ("is_approved", "is_active", "is_officially_verified", "city")
    # Add search functionality
    search_fields = ("name", "pincode", "city")
    # Control which fields are editable directly from the list view (use with caution)
    # list_editable = ('is_approved', 'is_active')
    # Order by name by default
    ordering = ("name",)


@admin.register(CommunitySuggestion)  # Use decorator for registration
class CommunitySuggestionAdmin(admin.ModelAdmin):
    # Customize list display for Suggestions
    list_display = (
        "suggested_name",
        "city",
        "pincode",
        "status",
        "description",
        "suggested_by_link",
        "created_at",
        "reviewed_at",
    )
    # Add filters
    list_filter = ("status", "city")
    # Add search
    search_fields = (
        "suggested_name",
        "pincode",
        "city",
        "suggested_by__username",
    )  # Search by suggester's username
    # Make the status field easily updatable
    list_editable = ("status",)
    # Fields to display when viewing/editing a single suggestion
    fields = (
        "suggested_name",
        "city",
        "pincode",
        "suggested_by",
        "status",
        "description",
        "admin_notes",
        "created_community",
        "created_at",
        "reviewed_at",
    )
    # Make some fields read-only in the detail view
    readonly_fields = ("suggested_by", "created_at", "reviewed_at")
    # Order by status then creation date
    ordering = ("status", "-created_at")
    # Add custom actions
    actions = ["approve_selected_suggestions"]

    # Helper function to make suggested_by clickable (optional)
    @admin.display(description="Suggested By")
    def suggested_by_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html

        if obj.suggested_by:
            link = reverse("admin:auth_user_change", args=[obj.suggested_by.id])
            return format_html('<a href="{}">{}</a>', link, obj.suggested_by.username)
        return None

    @admin.action(description="Approve selected suggestions and create Community")
    def approve_selected_suggestions(self, request, queryset):
        """
        Admin action to approve suggestions and create corresponding Community entries.
        """
        pending_suggestions = queryset.filter(
            status=CommunitySuggestion.SuggestionStatus.PENDING
        )
        approved_count = 0
        already_approved_count = queryset.count() - pending_suggestions.count()

        for suggestion in pending_suggestions:
            # Check if a similar community already exists (basic check)
            community_exists = Community.objects.filter(
                name__iexact=suggestion.suggested_name,
                city__iexact=suggestion.city,
                pincode=suggestion.pincode,
            ).exists()

            if not community_exists:
                # Create the new Community
                new_community = Community.objects.create(
                    name=suggestion.suggested_name,
                    city=suggestion.city,
                    description=suggestion.description,
                    pincode=suggestion.pincode,
                    is_approved=True,  # Approve it
                    is_active=True,  # Make it active
                )
                # Update the suggestion
                suggestion.status = CommunitySuggestion.SuggestionStatus.APPROVED
                suggestion.created_community = (
                    new_community  # Link the created community
                )
                suggestion.reviewed_at = (
                    timezone.now()
                )  # Import timezone: from django.utils import timezone
                suggestion.admin_notes = (
                    suggestion.admin_notes or ""
                ) + f"\nApproved by {request.user.username} via admin action."
                suggestion.save()
                approved_count += 1
            else:
                # Optionally update status to REJECTED_DUPLICATE or just leave pending with a note
                messages.warning(
                    request,
                    f"Suggestion '{suggestion.suggested_name}' ignored: A similar community already exists.",
                )
                # suggestion.status = CommunitySuggestion.SuggestionStatus.REJECTED_DUPLICATE
                # suggestion.admin_notes = (suggestion.admin_notes or '') + f"\nRejected as duplicate by {request.user.username} via admin action."
                # suggestion.reviewed_at = timezone.now()
                # suggestion.save()

        if approved_count > 0:
            # Use ngettext for pluralization
            msg = ngettext(
                f"{approved_count} suggestion was successfully approved and its Community created.",
                f"{approved_count} suggestions were successfully approved and their Communities created.",
                approved_count,
            )
            self.message_user(request, msg, messages.SUCCESS)
        if already_approved_count > 0:
            msg = ngettext(
                f"{already_approved_count} suggestion was ignored as it was not pending.",
                f"{already_approved_count} suggestions were ignored as they were not pending.",
                already_approved_count,
            )
            self.message_user(request, msg, messages.WARNING)


# Make sure to import timezone at the top: from django.utils import timezone
