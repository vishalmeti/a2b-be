# apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model # Use this to get the active User model
# Import the UserProfile model from the current app's models.py
from .models import UserProfile

# Get the active User model (usually django.contrib.auth.models.User)
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """ Serializer for the base Django User model (read-only fields for profile view) """
    class Meta:
        model = User
        # Fields commonly needed by the frontend for display
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        # Usually, you don't want to update these base fields directly via the profile
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserProfile model.
    Used for the /api/v1/users/me/ endpoint.
    """
    # Nest the read-only User details within the profile data
    user = UserSerializer(read_only=True)

    # --- Community fields OMITTED for now ---
    # Will be added later once the ForeignKey is added to the UserProfile model
    # community_id = serializers.PrimaryKeyRelatedField(...)
    # community_name = serializers.CharField(...)
    # --- End of omitted fields ---

    class Meta:
        model = UserProfile
        # List the fields from UserProfile model you want to expose/update via the /me endpoint
        fields = [
            'user', # The nested User object from UserSerializer above
            'phone_number',
            'address_details',
            'is_community_member_verified', # Read-only, likely set by admin/system
            'average_lender_rating', # Read-only, calculated field
            'average_borrower_rating', # Read-only, calculated field
            'updated_at', # Read-only
        ]
        # Specify fields that should *not* be updatable via a PUT/PATCH to /me/
        read_only_fields = [
            'user',
            'is_community_member_verified',
            'average_lender_rating',
            'average_borrower_rating',
            'updated_at',
        ]

