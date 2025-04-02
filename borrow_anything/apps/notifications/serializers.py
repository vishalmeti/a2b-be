# apps/notifications/serializers.py

from rest_framework import serializers

# Import models from relevant apps
from .models import Notification
from apps.users.models import UserProfile
# Import related models if needed for source lookups
# from apps.transactions.models import BorrowingRequest
# from apps.items.models import Item

# Optional: Basic serializer for the 'actor' field
class ActorProfileSerializer(serializers.ModelSerializer):
    """ Basic representation of the user profile who acted """
    username = serializers.CharField(source='user.username', read_only=True)
    # TODO: Add profile picture URL later if needed (using pre-signed URL logic)
    # profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['user_id', 'username'] # user_id is the PK (user.id)



class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Notification model.
    Formats notification data and allows updating the 'is_read' status.
    """
    # Nested representation of the actor (optional, can be null)
    actor = ActorProfileSerializer(read_only=True, allow_null=True)
    # Human-readable version of the notification type
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    # Include IDs of related objects for frontend linking/context
    related_request_id = serializers.IntegerField(source='related_request.id', read_only=True, allow_null=True)
    related_item_id = serializers.IntegerField(source='related_item.id', read_only=True, allow_null=True)
    related_item_title = serializers.CharField(source='related_item.title', read_only=True, allow_null=True) # Convenience
    related_user_profile_id = serializers.IntegerField(source='related_user_profile.id', read_only=True, allow_null=True)
    related_user_username = serializers.CharField(source='related_user_profile.user.username', read_only=True, allow_null=True) # Convenience

    class Meta:
        model = Notification
        fields = [
            'id',
            'actor', # Nested actor info
            'message',
            'notification_type', # The code (e.g., 'REQ_ACC')
            'notification_type_display', # Human-readable (e.g., 'Request Accepted')
            'is_read', # Writable via PATCH
            'created_at',
            # Related object IDs and convenience fields
            'related_request_id',
            'related_item_id',
            'related_item_title',
            'related_user_profile_id',
            'related_user_username',
            # Exclude 'recipient' as it's implicit (the user fetching their notifications)
        ]
        # Most fields are read-only except for 'is_read' which we want to update
        read_only_fields = [
            'id', 'actor', 'message', 'notification_type',
            'notification_type_display', 'created_at',
            'related_request_id', 'related_item_id', 'related_item_title',
            'related_user_profile_id', 'related_user_username',
        ]
        # 'is_read' is intentionally NOT read-only to allow PATCH updates

