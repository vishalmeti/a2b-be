# apps/items/views.py

# Import necessary mixins
from rest_framework import viewsets, permissions, filters, mixins, generics
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from .models import Item, Category, ItemImage
from .serializers import (
    ItemImageSerializer,
    ItemSerializer,
    ItemListSerializer,
    ItemCreateUpdateSerializer,
    CategorySerializer,
)
from .permissions import IsOwnerOrReadOnly
import boto3
import uuid
import os
from django.shortcuts import get_object_or_404
from django.utils.text import slugify  # For cleaning names for the key
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.conf import settings
from botocore.exceptions import ClientError


# Refactor CategoryViewSet using GenericViewSet + Mixins
class CategoryViewSet(
    mixins.ListModelMixin,  # Provides .list()
    mixins.RetrieveModelMixin,  # Provides .retrieve()
    viewsets.GenericViewSet,
):  # Base + generic API methods (get_queryset etc.)
    """
    API endpoint for viewing Categories (Read-Only).
    Lists only active categories. Based on GenericViewSet.
    """

    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


# Refactor ItemViewSet using GenericViewSet + Mixins
class ItemViewSet(
    mixins.ListModelMixin,  # Provides .list()
    mixins.CreateModelMixin,  # Provides .create()
    mixins.RetrieveModelMixin,  # Provides .retrieve()
    mixins.UpdateModelMixin,  # Provides .update() and .partial_update()
    mixins.DestroyModelMixin,  # Provides .destroy()
    viewsets.GenericViewSet,
):  # Base + generic API methods
    """
    API endpoint for Items: List, Create, Retrieve, Update, Destroy.
    Based on GenericViewSet with all standard CRUD mixins included.
    Handles filtering by community (implicit), category, search.
    """

    serializer_class = ItemSerializer  # Default serializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["category"]
    search_fields = ["title", "description"]

    # --- The internal logic remains the same as before ---

    def get_queryset(self):
        """Filter items to only show those in the user's community by default."""
        user = self.request.user
        user_profile = getattr(user, "profile", None)
        if not user_profile or not user_profile.community:
            return Item.objects.none()

        queryset = (
            Item.objects.filter(community=user_profile.community, is_active=True)
            .select_related("owner_profile__user", "category", "community")
            .prefetch_related("images")
        )
        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        # Use self.action provided by ViewSetMixin (available via GenericViewSet)
        action = getattr(
            self, "action", None
        )  # Use getattr for safety, though action should exist
        if action == "list":
            return ItemListSerializer
        if action in ["create", "update", "partial_update"]:
            return ItemCreateUpdateSerializer
        # Default for 'retrieve' or if action is None
        return ItemSerializer

    def perform_create(self, serializer):
        """Assign owner and community automatically when creating an item."""
        user_profile = getattr(self.request.user, "profile", None)
        if not user_profile or not user_profile.community:
            raise PermissionDenied("You must belong to a community to list an item.")
        serializer.save(owner_profile=user_profile, community=user_profile.community)


class ItemImageUploadView(generics.CreateAPIView):
    """
    Handles uploading images for a specific Item (identified by item_pk in URL)
    and creates the corresponding ItemImage record with the generated S3 key.

    Expects POST request with multipart/form-data containing:
    - 'image': The image file itself.
    - 'caption': (Optional) A caption for the image.
    """

    serializer_class = ItemImageSerializer  # Used for the response serialization
    permission_classes = [permissions.IsAuthenticated]  # Must be logged in

    def get_item_object(self, item_pk):
        """Helper method to get the item and check ownership permission"""
        user_profile = getattr(self.request.user, "profile", None)
        if not user_profile:
            raise PermissionDenied("User profile not found.")  # Or handle differently

        # Get the item this image belongs to
        item = get_object_or_404(Item, pk=item_pk)

        # Verify the user requesting the upload owns the item
        if item.owner_profile != user_profile:
            raise PermissionDenied(
                "You do not have permission to add images to this item."
            )
        return item

    def post(self, request, *args, **kwargs):
        """Handles the POST request with the image file upload."""
        item_pk = self.kwargs.get("item_pk")  # Get item ID from URL kwarg
        item_instance = self.get_item_object(item_pk)  # Gets item and checks permission

        image_file = request.FILES.get(
            "image"
        )  # 'image' is the expected field name in form-data
        caption = request.data.get("caption", "")  # Get optional caption from form data

        if not image_file:
            return Response(
                {"detail": "No image file provided in 'image' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- 1. Construct the S3 Key ---
        # We'll use a structure like: media/item_images/<item_slug_or_id>/<uuid>_<sanitized_filename>
        item_identifier = (
            slugify(item_instance.title)
            if item_instance.title
            else str(item_instance.id)
        )
        original_filename = image_file.name
        filename_base, filename_ext = os.path.splitext(original_filename)
        # Sanitize base filename and add UUID to prevent collisions
        sanitized_filename_base = slugify(filename_base)
        # Generate unique part AFTER sanitizing to avoid issues with '.' in UUIDs before ext
        unique_id = uuid.uuid4().hex[:8]  # Short UUID for brevity
        unique_filename = f"{sanitized_filename_base}-{unique_id}{filename_ext}"

        # Get base path from settings (e.g., 'media')
        s3_folder = getattr(
            settings, "AWS_LOCATION", "media"
        )  # Default to 'media' if not set
        s3_key = os.path.join(
            s3_folder, "item_images", str(item_instance.id), unique_filename
        )
        # Example key: media/item_images/123/my-cool-item-a1b2c3d4.jpg

        # --- 2. Upload to S3 using Boto3 ---
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        region = settings.AWS_S3_REGION_NAME
        # Determine ACL based on settings (None means private/default)
        acl = getattr(settings, "AWS_DEFAULT_ACL", None)

        if not bucket_name:
            # Log this properly in a real app
            print("ERROR: AWS_STORAGE_BUCKET_NAME not configured in settings.")
            return Response(
                {"detail": "S3 storage is not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            # Create Boto3 client (ensure credentials and region are configured)
            s3_client = boto3.client("s3", region_name=region)

            extra_args = {"ContentType": image_file.content_type}
            if acl:  # Only add ACL if it's explicitly set (like 'public-read')
                extra_args["ACL"] = acl

            # Use upload_fileobj for streaming upload from the request file
            s3_client.upload_fileobj(
                image_file,  # File object
                bucket_name,  # Bucket
                s3_key,  # Key (path/filename) in bucket
                # ExtraArgs=extra_args # Pass ACL, ContentType etc. if needed
            )
            # Log success (replace print with proper logging)
            print(f"Successfully uploaded {s3_key} to bucket {bucket_name}")

        except ClientError as e:
            # Log error (replace print with proper logging)
            print(f"ERROR: S3 Upload ClientError for key {s3_key}: {e}")
            return Response(
                {"detail": "Failed to upload image to storage."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            # Log unexpected errors (replace print with proper logging)
            print(f"ERROR: Unexpected error during S3 upload for key {s3_key}: {e}")
            return Response(
                {"detail": "An unexpected error occurred during upload."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --- 3. Create ItemImage Record ---
        # If upload was successful, create the database record
        item_image_instance = ItemImage.objects.create(
            item=item_instance,
            s3_key=s3_key,  # Store the generated key
            caption=caption,
        )

        # --- 4. Return Response ---
        # Serialize the created ItemImage record using the serializer defined for this view
        response_serializer = self.get_serializer(item_image_instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
