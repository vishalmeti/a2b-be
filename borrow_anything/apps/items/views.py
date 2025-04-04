# apps/items/views.py

# Import necessary mixins
from rest_framework import viewsets, permissions, filters, mixins, generics
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from apps.users.utils import S3ImageUploader

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

        user_id = self.request.query_params.get("user_id", None)

        queryset = (
            Item.objects.filter(community=user_profile.community)
            .select_related("owner_profile__user", "category", "community")
            .prefetch_related("images")
        )

        if user_id:
            return queryset.filter(owner_profile__user_id=user_id)

        return queryset.filter(is_active=True)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        # Use self.action provided by ViewSetMixin (available via GenericViewSet)
        action = getattr(
            self, "action", None
        )  # Use getattr for safety, though action should exist
        if action == "list":
            return ItemListSerializer
        if action in ["create", "update"]:
            return ItemCreateUpdateSerializer
        # Default for 'retrieve' or if action is None
        return ItemSerializer

    def perform_create(self, serializer):
        """Assign owner and community automatically when creating an item."""
        user_profile = getattr(self.request.user, "profile", None)
        if not user_profile or not user_profile.community:
            raise PermissionDenied("You must belong to a community to list an item.")
        serializer.save(owner_profile=user_profile, community=user_profile.community)

    def create(self, request, *args, **kwargs):
        """Override create to attach images directly during item creation."""
        request.data["is_active"] = True  # Ensure item is active by default
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        item_instance = serializer.instance
 # Debugging breakpoint
        # Check for 'images' in the uploaded files (handle multiple files)
        image_files = request.FILES.getlist("images")
        if image_files:
            s3Helper = S3ImageUploader()
            for image in image_files:
                unique_id = uuid.uuid4().hex[:8]  # Short UUID for uniqueness
                s3_key = f"items/{item_instance.pk}/{unique_id}"
                s3Helper.upload_image(image, s3_key)
                # Create the corresponding ItemImage record
                ItemImage.objects.create(
                    item=item_instance,
                    s3_key=s3_key,
                )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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
        s3Helper = S3ImageUploader()  # Initialize S3 uploader
        image_file_list = request.FILES.getlist(
            "images"
        )  # 'image' is the expected field name in form-data
        caption = request.data.get("caption", "")  # Get optional caption from form data

        if not image_file_list:
            return Response(
                {"detail": "No image file provided in 'image' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- 1. Construct the S3 Key ---

        for image_file in image_file_list:
            unique_id = uuid.uuid4().hex[:8]  # Short UUID
            s3_key = f"items/{item_pk}/{unique_id}"
            
            s3Helper.upload_image(
                image_file, s3_key
            )  # Upload the image to S3

            # --- 2. Create ItemImage instance ---
            item_image_instance = ItemImage.objects.create(
                item=item_instance,
                s3_key=s3_key,  # Store the generated key
                caption=caption,
            )




        # --- 3. Return Response ---
        # Serialize the created ItemImage record using the serializer defined for this view
        response_serializer = self.get_serializer(item_image_instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
