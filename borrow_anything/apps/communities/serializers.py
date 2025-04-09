# apps/communities/serializers.py
from rest_framework import serializers
from .models import Community, CommunitySuggestion

class CommunitySerializer(serializers.ModelSerializer):
    """
    Serializer for the Community model (Read-Only for regular users).
    Exposes fields relevant for listing/selection.
    """
    class Meta:
        model = Community
        fields = [
            'id',
            'name',
            'city',
            'pincode',
            'description',
            'latitude',       # Optional: useful for map features
            'longitude',      # Optional: useful for map features
            'is_officially_verified', # Might be useful info for users
        ]
        # Regular users cannot modify communities via this API
        read_only_fields = fields


class CommunitySuggestionSerializer(serializers.ModelSerializer):
    """
    Serializer for CREATING new community suggestions.
    """
    # Make suggested_by read-only; it will be set automatically from the request user.
    # We don't include status or admin_notes as these are not set by the user on creation.
    class Meta:
        model = CommunitySuggestion
        fields = [
            'id',               # Returned in response after creation
            'suggested_name',
            'description',
            'latitude',
            'longitude',
            'city',
            'pincode',
            # 'suggested_by' is set in the view, not sent by the client
        ]
        read_only_fields = ['id'] # ID is assigned on creation

    def validate_suggested_name(self, value):
        # Basic validation example
        if len(value) < 3:
            raise serializers.ValidationError("Community name must be at least 3 characters long.")
        # Could add checks for profanity etc. here
        return value

    # We will set 'suggested_by' in the view's perform_create method