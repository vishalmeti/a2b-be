# apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model # Use this to get the active User model
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile
from apps.communities.models import Community

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

    community = serializers.PrimaryKeyRelatedField(
        queryset=Community.objects.filter(
            is_approved=True, is_active=True
        ),  # Only allow setting to valid communities
        allow_null=True,  # Allow unsetting community if needed
        required=False,  # Not required for every profile update (e.g., updating phone only)
    )
    # Keep community_name read-only if you want to display it alongside the ID in GET responses
    community_name = serializers.CharField(
        source="community.name", read_only=True, allow_null=True
    )

    class Meta:
        model = UserProfile
        # List the fields from UserProfile model you want to expose/update via the /me endpoint
        fields = [
            "user",  # The nested User object from UserSerializer above
            "phone_number",
            "profile_picture_s3_key",  # Use the key field name
            # Include the 'community' field (writable ID)
            "community",
            # Read-only name for convenience in GET responses
            "community_name",
            "address_details",
            "is_community_member_verified",  # Read-only, likely set by admin/system
            "average_lender_rating",  # Read-only, calculated field
            "average_borrower_rating",  # Read-only, calculated field
            "updated_at",  # Read-only
        ]
        # Specify fields that should *not* be updatable via a PUT/PATCH to /me/
        read_only_fields = [
            "user",
            "community_name",
            "is_community_member_verified",
            "average_lender_rating",
            "average_borrower_rating",
            "updated_at",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new User instances. Handles password hashing
    and automatic UserProfile creation.
    """

    # Define password field specifically for input validation and hashing
    password = serializers.CharField(
        write_only=True,  # Password should not be sent back in the response
        required=True,
        validators=[validate_password],  # Apply Django's built-in password validators
        style={
            "input_type": "password"
        },  # Helps DRF Browsable API render as password input
    )

    class Meta:
        model = User  # Target the built-in User model
        # Fields required for user creation
        fields = (
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
        )
        extra_kwargs = {
            # Make email required for registration
            "email": {"required": True},
            # Optional: Make first/last names not required during signup
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
        }

    def create(self, validated_data):
        """
        Create and return a new `User` instance, given the validated data.
        Also creates the associated UserProfile.
        """

        # Use create_user to handle password hashing automatically
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],  # create_user handles hashing
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )

        # Automatically create the linked UserProfile
        # This assumes UserProfile doesn't require any extra fields during creation
        UserProfile.objects.create(user=user)

        return user
