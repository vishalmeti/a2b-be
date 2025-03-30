# apps/transactions/views.py

from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Q  # For OR queries
from django.utils import timezone  # For setting timestamps

# Import local models and serializers
from .models import BorrowingRequest, Review
from .serializers import (
    BorrowingRequestSerializer,
    BorrowingRequestCreateSerializer,
    # ReviewSerializer # Import later when needed
)

# Import models from other apps if needed for checks
from apps.items.models import Item

# Import UserProfile if needed for type hinting or direct access (though request.user.profile is used)
# from apps.users.models import UserProfile


# Permissions (Defined here for clarity, could be in permissions.py)
class IsBorrowerOrLender(permissions.BasePermission):
    """Allows access only if user is the borrower or the lender"""

    def has_object_permission(self, request, view, obj):
        # Ensure the user has a profile before checking ownership
        user_profile = getattr(request.user, "profile", None)
        # Check if the user's profile matches either the borrower or lender profile
        return user_profile and (
            obj.borrower_profile == user_profile or obj.lender_profile == user_profile
        )


class IsLender(permissions.BasePermission):
    """Allows access only if user is the lender"""

    def has_object_permission(self, request, view, obj):
        user_profile = getattr(request.user, "profile", None)
        return user_profile and obj.lender_profile == user_profile


class IsBorrower(permissions.BasePermission):
    """Allows access only if user is the borrower"""

    def has_object_permission(self, request, view, obj):
        user_profile = getattr(request.user, "profile", None)
        return user_profile and obj.borrower_profile == user_profile


# The ViewSet using GenericViewSet + Mixins
class BorrowingRequestViewSet(
    mixins.ListModelMixin,  # Provides .list() method for GET /requests/
    mixins.RetrieveModelMixin,  # Provides .retrieve() method for GET /requests/{pk}/
    mixins.CreateModelMixin,  # Provides .create() method for POST /requests/
    viewsets.GenericViewSet,
):  # Base class providing core functionality
    """
    ViewSet for managing Borrowing Requests.
    Handles List, Retrieve, Create via mixins mapped manually in urls.py.
    Custom actions needed for status updates.
    """

    serializer_class = BorrowingRequestSerializer  # Default for list/retrieve
    permission_classes = [
        permissions.IsAuthenticated
    ]  # Base permission for all actions

    def get_queryset(self):
        """
        Filter requests to only show those involving the current user
        (either as borrower or lender). Accessed by the .list() method.
        """
        user_profile = getattr(self.request.user, "profile", None)
        if not user_profile:
            return BorrowingRequest.objects.none()

        return (
            BorrowingRequest.objects.filter(
                Q(borrower_profile=user_profile) | Q(lender_profile=user_profile)
            )
            .select_related(
                "item__owner_profile__user",
                "item__category",
                "borrower_profile__user",
                "lender_profile__user",
            )
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action (method name)."""
        # self.action is set based on the method mapping in urls.py
        # e.g., for POST to /requests/, action will be 'create'
        if self.action == "create":
            return BorrowingRequestCreateSerializer
        # Default for 'list', 'retrieve'
        return BorrowingRequestSerializer

    def get_permissions(self):
        """Apply stricter permissions for retrieving a specific request detail."""
        if self.action == "retrieve":
            # Must be Authenticated AND either the Borrower or Lender
            return [permissions.IsAuthenticated(), IsBorrowerOrLender()]
        # Default permissions (IsAuthenticated) apply to 'list' and 'create'
        return super().get_permissions()

    def perform_create(self, serializer):
        """
        Set borrower and lender automatically on creation.
        Called by .create() method (from CreateModelMixin).
        """
        item = serializer.validated_data["item"]
        borrower_profile = getattr(self.request.user, "profile", None)
        # Lender is derived from the validated item
        lender_profile = item.owner_profile

        if not borrower_profile:
            raise PermissionDenied("User profile required to make a request.")
        # Lender profile should exist if item validation passed, but check doesn't hurt
        if not lender_profile:
            raise ValidationError("Item owner profile could not be determined.")

        # Pass request context to serializer (already done by default in get_serializer_context)
        # The CreateSerializer's validate method checks self-borrowing etc.
        # Save the instance with borrower and lender set.
        serializer.save(
            borrower_profile=borrower_profile, lender_profile=lender_profile
        )
        # TODO (later): Trigger 'New Request' Notification (e.g., via signal)

    # --- Placeholders for Custom Actions (Status Updates) ---
    # These will be implemented next using @action decorator.
    # The manual URL mapping will need corresponding entries for these actions.

    # @action(detail=True, methods=['patch'], permission_classes=[IsLender], url_path='accept')
    # def accept(self, request, pk=None): ...

    # @action(detail=True, methods=['patch'], permission_classes=[IsLender], url_path='decline')
    # def decline(self, request, pk=None): ...

    # @action(detail=True, methods=['patch'], permission_classes=[IsBorrower], url_path='cancel')
    # def cancel(self, request, pk=None): ...

    # @action(detail=True, methods=['patch'], permission_classes=[IsBorrower], url_path='confirm-pickup')
    # def confirm_pickup(self, request, pk=None): ...

    # @action(detail=True, methods=['patch'], permission_classes=[IsBorrower], url_path='confirm-return')
    # def confirm_return(self, request, pk=None): ...

    # @action(detail=True, methods=['patch'], permission_classes=[IsLender], url_path='complete')
    # def complete(self, request, pk=None): ...

    # --- View for Reviews needed later ---
