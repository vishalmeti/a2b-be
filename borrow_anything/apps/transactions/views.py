# apps/transactions/views.py

# Django imports
from django.db.models import Q
from django.utils import timezone

# Django REST Framework imports
from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

# Local imports
from .models import BorrowingRequest, Review
from .serializers import (
    BorrowingRequestSerializer,
    BorrowingRequestCreateSerializer,
    ReviewSerializer,
)
from apps.items.models import Item
from apps.users.models import UserProfile  # Import UserProfile

from .permissions import IsReviewParticipant


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
        # obj is BorrowingRequest instance
        return user_profile and obj.lender_profile == user_profile


class IsBorrower(permissions.BasePermission):
    """Allows access only if user is the borrower"""

    def has_object_permission(self, request, view, obj):
        user_profile = getattr(request.user, "profile", None)
        # obj is BorrowingRequest instance
        return user_profile and obj.borrower_profile == user_profile


class IsReviewParticipant(permissions.BasePermission):
    """
    Object-level permission to only allow borrower or lender of the associated
    borrowing request to view/edit the review.
    """

    def has_object_permission(self, request, view, obj):
        # obj here is the Review instance
        user_profile = getattr(request.user, "profile", None)
        if hasattr(obj, "borrowing_request"):
            return user_profile and (
                obj.borrowing_request.borrower_profile == user_profile
                or obj.borrowing_request.lender_profile == user_profile
            )
        return False


class IsLender(permissions.BasePermission):
    """Allows access only if user is the lender"""

    def has_permission(self, request, view):
        print("IsLender: Checking class-level permission")
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        print("IsLender: Checking object-level permission")
        user_profile = getattr(request.user, "profile", None)
        print(f"User Profile: {user_profile}, Lender Profile: {obj.lender_profile}")
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
        """Apply appropriate permissions based on the action."""
        print(f"Getting permissions for action: {self.action}")
        if self.action == "retrieve":
            return [permissions.IsAuthenticated(), IsBorrowerOrLender()]
        elif self.action in ["accept", "decline", "complete"]:
            return [permissions.IsAuthenticated(), IsLender()]
        elif self.action in ["cancel", "confirm_pickup", "confirm_return"]:
            # Borrower can cancel or confirm pickup
            return [permissions.IsAuthenticated(), IsBorrower()]
        # return [permissions.IsAuthenticated()]
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

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsLender],
        url_path="accept",
    )
    def accept(self, request, pk=None):
        """Lender accepts the borrowing request."""
        instance = (
            self.get_object()
        )  # Gets BorrowingRequest by pk, checks base permissions

        # 1. Check current status
        if instance.status != BorrowingRequest.StatusChoices.PENDING:
            return Response(
                {"detail": "Request is not pending approval."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # get the item from the request and change its status to 'BORBOOKEDROWED'
        item = instance.item
        if item.availability_status != Item.AvailabilityStatus.BOOKED:
            item.availability_status = Item.AvailabilityStatus.BOOKED
            item.save(update_fields=["availability_status", "updated_at"])
        else:
            return Response(
                {"detail": "Item is already borrowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # 2. Update status and timestamp
        instance.status = BorrowingRequest.StatusChoices.ACCEPTED
        instance.processed_at = timezone.now()
        # Optionally save a message if provided
        lender_message = request.data.get("lender_response_message")
        if lender_message:
            instance.lender_response_message = lender_message
        instance.save()

        # 3. *** Auto-Decline Conflicting PENDING Requests ***
        conflicting_requests = BorrowingRequest.objects.filter(
            item=instance.item,  # Same item
            status=BorrowingRequest.StatusChoices.PENDING,  # Only pending ones
            start_date__lte=instance.end_date,  # Their start <= accepted end
            end_date__gte=instance.start_date,  # Their end >= accepted start
        ).exclude(
            pk=instance.pk
        )  # Exclude the one just accepted

        declined_count = 0
        for req in conflicting_requests:
            req.status = BorrowingRequest.StatusChoices.DECLINED
            req.processed_at = timezone.now()
            req.lender_response_message = (
                "Item automatically declined as it was booked for conflicting dates."
            )
            req.save(
                update_fields=[
                    "status",
                    "processed_at",
                    "lender_response_message",
                    "updated_at",
                ]
            )
            declined_count += 1
            # TODO (Signal): Trigger 'Request Declined' Notification for req.borrower_profile

        if declined_count > 0:
            print(
                f"Auto-declined {declined_count} conflicting requests for item {instance.item.id}"
            )  # Replace with logging

        # TODO (Signal): Trigger 'Request Accepted' Notification for instance.borrower_profile

        # 4. Return updated data
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsLender],
        url_path="decline",
    )
    def decline(self, request, pk=None):
        """Lender declines the borrowing request."""
        instance = self.get_object()

        # 1. Check current status
        if instance.status != BorrowingRequest.StatusChoices.PENDING:
            return Response(
                {"detail": "Request is not pending approval."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Update status and timestamp
        instance.status = BorrowingRequest.StatusChoices.DECLINED
        instance.processed_at = timezone.now()
        # Optionally save the reason/message
        lender_message = request.data.get("lender_response_message")
        if lender_message:
            instance.lender_response_message = lender_message
        instance.save()

        # TODO (Signal): Trigger 'Request Declined' Notification for instance.borrower_profile

        # 3. Return updated data
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsBorrower],
        url_path="cancel",
    )
    def cancel(self, request, pk=None):
        """Borrower cancels the request (allowed if PENDING or ACCEPTED)."""
        instance = self.get_object()  # Checks object permissions via decorator

        # Check if cancellable
        if instance.status not in [
            BorrowingRequest.StatusChoices.PENDING,
            BorrowingRequest.StatusChoices.ACCEPTED,
        ]:
            return Response(
                {
                    "detail": f"Request cannot be cancelled when status is {instance.status}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update status
        instance.status = BorrowingRequest.StatusChoices.CANCELLED_BORROWER
        instance.processed_at = timezone.now()

        # Optionally update item availability status
        item = instance.item
        if item.availability_status in [
            Item.AvailabilityStatus.BORROWED,
            Item.AvailabilityStatus.BOOKED,
        ]:
            item.availability_status = Item.AvailabilityStatus.AVAILABLE
            item.save(update_fields=["availability_status", "updated_at"])

        # Optionally save the reason/message
        borrower_message = request.data.get("borrower_response_message")
        if borrower_message:
            instance.borrower_response_message = borrower_message
        instance.save(update_fields=["status", "updated_at"])

        # TODO (Signal): Trigger 'Request Cancelled' Notification for lender

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsBorrower],
        url_path="confirm-pickup",
    )
    def confirm_pickup(self, request, pk=None):
        """Borrower confirms they have picked up the item."""
        instance = self.get_object()  # Checks object permissions

        # Check if status is ACCEPTED
        if instance.status != BorrowingRequest.StatusChoices.ACCEPTED:
            return Response(
                {
                    "detail": f"Pickup can only be confirmed if request is ACCEPTED (current: {instance.status})."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update status and timestamp
        instance.status = BorrowingRequest.StatusChoices.PICKED_UP
        instance.pickup_confirmed_at = timezone.now()
        instance.save(update_fields=["status", "pickup_confirmed_at", "updated_at"])

        # Update Item's availability status
        try:
            item = instance.item
            item.availability_status = Item.AvailabilityStatus.BORROWED
            item.save(update_fields=["availability_status"])
        except Item.DoesNotExist:
            # Should not happen if request exists, but handle defensively
            pass  # Or log an error
        except Exception as e:
            # Log error during item update
            print(
                f"Error updating item status for request {instance.id}: {e}"
            )  # Use proper logging

        # TODO (Signal): Trigger 'Item Picked Up' Notification for lender

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # --- *** Add Return/Complete Actions *** ---

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsBorrower],
        url_path="confirm-return",
    )
    def confirm_return(self, request, pk=None):
        """Borrower confirms they have returned the item (pending lender confirmation)."""
        instance = self.get_object()  # Checks permissions

        # Check if status allows this action
        if instance.status != BorrowingRequest.StatusChoices.PICKED_UP:
            return Response(
                {
                    "detail": f"Return can only be confirmed if status is PICKED_UP (current: {instance.status})."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update status and timestamp
        instance.status = BorrowingRequest.StatusChoices.RETURNED
        instance.return_initiated_at = timezone.now()
        instance.save(update_fields=["status", "return_initiated_at", "updated_at"])

        # TODO (Signal): Trigger 'Item Returned' Notification for lender

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsLender],
        url_path="complete",
    )
    def complete(self, request, pk=None):
        """Lender confirms item returned okay, completing the transaction."""
        instance = self.get_object()  # Checks permissions

        # Check if status allows this action
        if instance.status != BorrowingRequest.StatusChoices.RETURNED:
            return Response(
                {
                    "detail": f"Request can only be completed if status is RETURNED (current: {instance.status})."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update status and timestamp
        instance.status = BorrowingRequest.StatusChoices.COMPLETED
        instance.completed_at = timezone.now()
        instance.save(update_fields=["status", "completed_at", "updated_at"])

        # Update Item's availability status back to AVAILABLE
        # Basic approach: Set it available. More complex: check future bookings?
        try:
            item = instance.item
            # TODO: Add logic here later if needed to check for other *accepted* future requests
            # before setting back to available. For now, assume it becomes available.
            item.availability_status = Item.AvailabilityStatus.AVAILABLE
            item.save(update_fields=["availability_status"])
        except Exception as e:
            print(
                f"Error updating item status to available for request {instance.id}: {e}"
            )  # Use logging

        # TODO (Signal): Trigger 'Transaction Completed' Notification for borrower
        # TODO (Signal): Trigger creation of Review object: Review.objects.get_or_create(borrowing_request=instance)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ReviewViewSet(
    mixins.RetrieveModelMixin,  # Provides .retrieve() method for GET
    mixins.UpdateModelMixin,  # Provides .update() & .partial_update() methods for PUT/PATCH
    viewsets.GenericViewSet,
):  # Base class
    """
    API endpoint for retrieving and updating a Review associated with a Borrowing Request.
    Uses GenericViewSet + Mixins.
    Accessed via /requests/<request_pk>/review/ (Requires manual URL mapping)
    Handles permission checks to ensure only borrower/lender can update their respective fields.
    """

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsReviewParticipant]
    # Look up the Review object using the 'borrowing_request_id' (which is the PK)
    # based on the 'request_pk' value captured from the URL.
    lookup_field = "borrowing_request_id"
    lookup_url_kwarg = "request_pk"

    def get_queryset(self):
        """
        Ensure we only retrieve reviews for COMPLETED requests
        accessible by the current user.
        """
        user_profile = getattr(self.request.user, "profile", None)
        if not user_profile:
            return Review.objects.none()

        # Base queryset: Reviews linked to completed requests involving the user
        completed_requests_qs = BorrowingRequest.objects.filter(
            status=BorrowingRequest.StatusChoices.COMPLETED
        ).filter(Q(borrower_profile=user_profile) | Q(lender_profile=user_profile))
        # Return reviews linked to those completed requests
        return Review.objects.filter(
            borrowing_request__in=completed_requests_qs
        ).select_related(
            "borrowing_request__item",
            "borrowing_request__borrower_profile__user",
            "borrowing_request__lender_profile__user",
        )

    def perform_update(self, serializer):
        """
        Custom logic run during update (called by UpdateModelMixin's update/partial_update).
        Ensures only the correct user updates their respective fields and sets submission timestamp.
        """
        # Debugging breakpoint
        instance = serializer.instance  # The Review object being updated/saved
        user_profile = getattr(self.request.user, "profile", None)
        borrowing_request = instance.borrowing_request

        # 1. Double check request is completed (primarily enforced by get_queryset)
        if borrowing_request.status != BorrowingRequest.StatusChoices.COMPLETED:
            raise ValidationError(
                "Reviews can only be submitted for completed requests."
            )

        now = timezone.now()
        save_kwargs = {}  # Arguments to pass to serializer.save()
        is_valid_role_update = (
            False  # Flag to track if user updated fields relevant to their role
        )

        # 2. Check user role and process role-specific fields
        if borrowing_request.borrower_profile == user_profile:
            # User is the Borrower
            if instance.borrower_review_submitted_at is not None:
                raise PermissionDenied(
                    "You have already submitted your review as the borrower."
                )

            # Check if borrower is submitting borrower-specific fields
            borrower_fields_submitted = any(
                f in serializer.validated_data
                for f in ["rating_for_lender", "comment_for_lender"]
            )

            if borrower_fields_submitted:
                is_valid_role_update = True
                save_kwargs["borrower_review_submitted_at"] = (
                    now  # Set timestamp via save kwargs
                )
            else:
                # If borrower submitted data, but *only* lender fields, this is invalid for *them*
                lender_fields_submitted_by_borrower = any(
                    f in serializer.validated_data
                    for f in [
                        "rating_for_borrower",
                        "comment_for_borrower",
                        "rating_for_item_condition_on_return",
                        "comment_on_item_condition",
                    ]
                )
                if lender_fields_submitted_by_borrower:
                    raise ValidationError(
                        "Borrower cannot submit ratings/comments for themselves or item condition."
                    )
                # If they submitted no review fields at all, allow save to proceed (might be updating other hypothetical fields)
                # If they submitted only invalid fields, serializer validation might catch some, but this logic prevents timestamp setting

        elif borrowing_request.lender_profile == user_profile:
            # User is the Lender
            if instance.lender_review_submitted_at is not None:
                raise PermissionDenied(
                    "You have already submitted your review as the lender."
                )

            # Check if lender is submitting lender-specific fields
            lender_fields_submitted = any(
                f in serializer.validated_data
                for f in [
                    "rating_for_borrower",
                    "comment_for_borrower",
                    "rating_for_item_condition_on_return",
                    "comment_on_item_condition",
                ]
            )

            if lender_fields_submitted:
                is_valid_role_update = True
                save_kwargs["lender_review_submitted_at"] = (
                    now  # Set timestamp via save kwargs
                )
            else:
                # If lender submitted data, but *only* borrower fields, this is invalid for *them*
                borrower_fields_submitted_by_lender = any(
                    f in serializer.validated_data
                    for f in ["rating_for_lender", "comment_for_lender"]
                )
                if borrower_fields_submitted_by_lender:
                    raise ValidationError(
                        "Lender cannot submit ratings/comments for themselves."
                    )

        else:
            # Should be caught by IsReviewParticipant permission class
            raise PermissionDenied("You are not a participant in this transaction.")

        # 3. Perform the save using the serializer
        # serializer.save() handles updating only the validated fields provided in the PATCH request.
        # We pass the timestamp to be set via kwargs.
        try:
            serializer.save(**save_kwargs)
        except Exception as e:
            # Catch potential errors during save and provide clearer feedback if needed
            print(
                f"Error saving review for request {instance.borrowing_request_id}: {e}"
            )  # Use logging
            raise  # Re-raise the original exception

        # 4. Update UserProfile ratings after successful save
        instance.refresh_from_db()  # Ensure we have the latest data
        borrowing_request = instance.borrowing_request

        # If borrower submitted review, update lender's rating
        if "borrower_review_submitted_at" in save_kwargs and instance.rating_for_lender is not None:
            lender_profile = borrowing_request.lender_profile
            if lender_profile:
                lender_profile.update_rating(instance.rating_for_lender)

        # If lender submitted review, update borrower's rating
        if "lender_review_submitted_at" in save_kwargs and instance.rating_for_borrower is not None:
            borrower_profile = borrowing_request.borrower_profile
            if borrower_profile:
                borrower_profile.update_rating(instance.rating_for_borrower)

        # TODO (Signal): Trigger 'Review Submitted' Notification?
