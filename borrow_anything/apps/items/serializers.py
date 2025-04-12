# apps/items/serializers.py

from rest_framework import serializers

from apps.users.serializers import UserProfileSerializer
from apps.communities.models import Community
from .models import Category, Item, ItemImage
from apps.users.models import UserProfile # Needed for owner info later if required
# Import UserProfileSerializer if needed for owner details later
# from apps.users.serializers import UserProfileSerializer
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from apps.users.utils import S3ImageUploader
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from rest_framework import serializers
from .models import ItemImage # Ensure ItemImage model is imported

class CategorySerializer(serializers.ModelSerializer):
    """ Serializer for the Category model (Read-Only) """
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon'] # Expose ID, name, and maybe an icon identifier
        read_only_fields = fields # Categories typically managed by admin


class ItemImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ItemImage
        fields = ['id', 'image_url', 'caption', 'uploaded_at'] # Replaced s3_key with image_url
        read_only_fields = ('id', 'uploaded_at', 'image_url')

    def get_image_url(self, obj):
        """ Calls the utility function to generate the pre-signed URL. """
        # obj is the ItemImage instance
        return S3ImageUploader().get_image_presigned_url(obj.s3_key)
class ItemSerializer(serializers.ModelSerializer):
    """ Serializer for the Item model (Detailed View) """
    # Nested read-only category info
    category = CategorySerializer(read_only=True)
    # Write-only field for setting category by ID on create/update
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source='category', write_only=True, allow_null=False # Category is mandatory
    )
    # Read-only owner user
    owner = serializers.SerializerMethodField()
    # Read-only community name
    community_name = serializers.CharField(source='community.name', read_only=True, allow_null=True) # Community should exist based on model clean()
    # Nested list of image references (S3 keys)
    images = ItemImageSerializer(many=True, read_only=True) # Images are typically managed via separate uploads

    def get_owner(self, obj):
        return UserProfileSerializer(obj.owner_profile).data
    class Meta:
        model = Item
        fields = [
            'id',
            'title',
            'description',
            'category',         # Read-only nested Category object
            'category_id',      # Write-only field for setting category
            'condition',
            'availability_status',
            'availability_notes',
            'deposit_amount',
            'borrowing_fee',
            'max_borrow_duration_days',
            'pickup_details',
            'is_active',
            'average_item_rating', # Read-only calculated field
            'owner',      # Read-only owner info
            'community_name',      # Read-only community info
            'images',              # List of associated image keys/captions
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'availability_status', # Should be updated via transaction logic mostly
            'average_item_rating',
            'owner',
            'community_name',
            'images',           # Handled separately
            'created_at',
            'updated_at',
        ]


class ItemListSerializer(serializers.ModelSerializer):
    """ Concise serializer for item lists """
    category = CategorySerializer(read_only=True)
    owner_username = serializers.CharField(source='owner_profile.user.username', read_only=True)
    community_name = serializers.CharField(source='community.name', read_only=True, allow_null=True)
    # Optional: Add primary image S3 key if you implement logic to determine it
    images = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()

    def get_owner(self, obj):
        return UserProfileSerializer(obj.owner_profile).data

    class Meta:
        model = Item
        fields = [ # Select fewer fields for list views
            'id',
            'title',
            "description",
            'category',
            'condition',
            'availability_status',
            'availability_notes',
            'deposit_amount',
            'max_borrow_duration_days',
            'pickup_details',
            'is_active',
            'borrowing_fee',
            'owner_username',
            'community_name',
            'average_item_rating',
            'images',
            'created_at',
            'owner'
        ]

    # Example for getting primary image key
    def get_images(self, obj):
        """ Gets the first associated ItemImage and generates its pre-signed URL. """
        # obj is the Item instance
        images_instance = ItemImage.objects.filter(item=obj) 
        images = []
        if images_instance.exists():
            for image in images_instance:
                images.append(
                    S3ImageUploader().get_image_presigned_url(image.s3_key)
                )
            return images
        return None


class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating the core Item data (excluding images).
    Images need separate handling due to using s3_key field.
    """
    # Make category settable via ID
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        allow_null=False # Category is mandatory
    )
    
    # Add community_id field to allow setting community by ID
    community_id = serializers.PrimaryKeyRelatedField(
        source='community',
        queryset=Community.objects.all(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Item
        # Fields that the owner can create or update
        fields = [
            'id',
            'title',
            'description',
            'category',
            'condition',
            'availability_notes',
            'deposit_amount',
            'borrowing_fee',
            'community_id', # Allow setting community by ID
            'max_borrow_duration_days',
            'pickup_details',
            'is_active', # Allow owner to deactivate/reactivate
        ]

    def validate_category(self, value):
        """ Ensure the selected category is active """
        if not value.is_active:
            raise serializers.ValidationError("Selected category is not active.")
        return value

    # NOTE: The 'owner_profile' field must be set in the view's perform_create method.
    # If 'community_id' is not provided, fall back to owner's community.
