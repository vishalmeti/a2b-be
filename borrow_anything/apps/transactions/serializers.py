# apps/transactions/serializers.py

from rest_framework import serializers
from django.utils import timezone # For validation
from django.contrib.auth import get_user_model

# Import models from relevant apps
from .models import BorrowingRequest, Review
from apps.items.models import Item
from apps.users.models import UserProfile

User = get_user_model()

# --- Helper Serializers (for nested representations) ---

class UserProfileBasicSerializer(serializers.ModelSerializer):
    """ Basic UserProfile info for nested display """
    username = serializers.CharField(source='user.username', read_only=True)
    # Add other fields if needed, e.g., average rating?
    class Meta:
        model = UserProfile
        fields = ['user_id', 'username'] # user_id is the primary key (user.id)


class ItemBasicSerializer(serializers.ModelSerializer):
    """ Basic Item info for nested display """
    owner_username = serializers.CharField(source='owner_profile.user.username', read_only=True)
    class Meta:
        model = Item
        fields = ['id', 'title', 'owner_username']


# --- Borrowing Request Serializers ---

class BorrowingRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for READING/displaying BorrowingRequest details.
    Includes nested basic info about the item, borrower, and lender.
    """
    # Use nested serializers for related objects
    item = ItemBasicSerializer(read_only=True)
    borrower_profile = UserProfileBasicSerializer(read_only=True)
    lender_profile = UserProfileBasicSerializer(read_only=True)
    # Include human-readable status display
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = BorrowingRequest
        # Include all relevant fields for display
        fields = [
            'id',
            'item',
            'borrower_profile',
            'lender_profile',
            'start_date',
            'end_date',
            'status',
            'status_display', # Human-readable status
            'borrower_message',
            'lender_response_message',
            'created_at',
            'updated_at',
            'processed_at', # When accepted/declined
            'pickup_confirmed_at',
            'return_initiated_at',
            'completed_at',
        ]
        read_only_fields = fields # This serializer is primarily for reading


class BorrowingRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for CREATING a new BorrowingRequest.
    Validates input data like dates and item availability.
    """
    # Use PrimaryKeyRelatedField for input, ensuring item exists and is available
    item = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.filter(
            is_active=True,
            availability_status=Item.AvailabilityStatus.AVAILABLE
        )
        # Add error message if needed: error_messages={'does_not_exist': 'Item not found or is unavailable.'}
    )

    class Meta:
        model = BorrowingRequest
        # Fields required from the user when creating a request
        fields = [
            'id',               # Read-only, returned after creation
            'item',             # Writable ID field
            'start_date',
            'end_date',
            'borrower_message', # Optional message
            # Read-only fields shown in response:
            'borrower_profile',
            'lender_profile',
            'status',
            'created_at'
        ]
        read_only_fields = [
            'id', 'borrower_profile', 'lender_profile', 'status', 'created_at'
        ]

    def validate(self, attrs):
        """
        Perform cross-field validation.
        """
        # 1. Check if dates are logical
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        today = timezone.now().date()

        if start_date < today:
            raise serializers.ValidationError({"start_date": "Start date cannot be in the past."})
        if end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be before the start date."})

        # 2. Check if requester is the item owner
        item = attrs.get('item')
        request = self.context.get('request') # Get request context from the view
        user_profile = getattr(request.user, 'profile', None)

        if not user_profile:
             # This should ideally be caught by view permissions, but double-check
             raise serializers.ValidationError("User profile not found for requester.")

        if item.owner_profile == user_profile:
            raise serializers.ValidationError("You cannot borrow your own item.")

        # 3. Check if item owner and borrower are in the same community (optional, but good for hyperlocal)
        if item.community != user_profile.community:
             raise serializers.ValidationError("Item is not available in your community.")

        # 4. Optional: Check for duration limits
        if item.max_borrow_duration_days:
            duration = (end_date - start_date).days + 1
            if duration > item.max_borrow_duration_days:
                raise serializers.ValidationError(
                    f"Requested duration ({duration} days) exceeds the maximum allowed ({item.max_borrow_duration_days} days) for this item."
                )

        # 5. Optional: Check for overlapping requests (more complex - might skip initial validation)
        # existing_requests = BorrowingRequest.objects.filter(...)
        # if existing_requests.exists():
        #    raise serializers.ValidationError("Item is already requested or booked for the selected dates.")

        return attrs

    # Note: The view calling this serializer will need to pass the 'request'
    # in the serializer context: serializer = BorrowingRequestCreateSerializer(data=..., context={'request': request})
    # The view will also set 'borrower_profile' and 'lender_profile' during save.


# --- Review Serializer ---

class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating/viewing Reviews.
    Permissions on who can write which fields need to be handled in the view.
    """
    # Include read-only info about the related request for context
    borrowing_request_id = serializers.IntegerField(source='borrowing_request.id', read_only=True)
    item_title = serializers.CharField(source='borrowing_request.item.title', read_only=True)
    borrower_username = serializers.CharField(source='borrowing_request.borrower_profile.user.username', read_only=True)
    lender_username = serializers.CharField(source='borrowing_request.lender_profile.user.username', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'borrowing_request_id', # Read-only context
            'item_title',           # Read-only context
            'borrower_username',    # Read-only context
            'lender_username',      # Read-only context

            # Fields for Borrower to submit
            'rating_for_lender',
            'comment_for_lender',
            'borrower_review_submitted_at', # Read-only timestamp

            # Fields for Lender to submit
            'rating_for_borrower',
            'comment_for_borrower',
            'rating_for_item_condition_on_return',
            'comment_on_item_condition',
            'lender_review_submitted_at', # Read-only timestamp

            'created_at', # Read-only
            'updated_at', # Read-only
        ]
        read_only_fields = [
            'id', 'borrowing_request_id', 'item_title', 'borrower_username', 'lender_username',
            'borrower_review_submitted_at', 'lender_review_submitted_at',
            'created_at', 'updated_at',
        ]

    # Note: Validation for who can write which fields (borrower vs lender)
    # will be handled in the associated view logic, likely by checking request.user
    # against borrowing_request.borrower_profile or borrowing_request.lender_profile.
    # We might split this into BorrowerReviewSerializer and LenderReviewSerializer later.