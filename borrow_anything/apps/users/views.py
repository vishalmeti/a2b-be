from django.shortcuts import render, get_object_or_404

# Create your views here.
# apps/users/views.py

from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile, UserCommunityMembership
from .serializers import UserProfileSerializer, UserCreateSerializer, UserCommunityMembershipSerializer
from django.contrib.auth import get_user_model
from .utils import S3ImageUploader
from apps.communities.models import Community
from rest_framework.exceptions import ValidationError
import uuid

User = get_user_model()

class ManageUserView(generics.RetrieveUpdateAPIView):
    """
    View to retrieve and update the profile of the currently authenticated user.
    Handles GET (retrieve) and PUT/PATCH (update) requests to /api/v1/users/me/.
    """

    serializer_class = UserProfileSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]  # Only logged-in users can access

    def get_object(self):
        """
        Override get_object to return the UserProfile linked to the request.user.
        Uses get_or_create to handle cases where a profile might not exist yet
        (e.g., if user was created before profile logic/signals were added).
        """
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        # You might want to log the 'created' status during development
        # if created:
        #     print(f"Created profile for user {self.request.user.username}")
        return profile

    # Note: By inheriting from RetrieveUpdateAPIView, this view automatically
    # handles GET (retrieve profile), PUT (full update), and PATCH (partial update)
    # based on the UserProfileSerializer definition. Ensure the serializer's
    # read_only_fields are set appropriately to control what can be updated.


class UserCreateView(generics.CreateAPIView):
    """
    View to create (register) a new user. Handles POST requests.
    Accessible by any user (authenticated or not).
    """

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    # Allow any user (even anonymous) to access this endpoint to register
    permission_classes = [permissions.AllowAny]

    # The CreateAPIView handles everything needed for a POST request:
    # 1. It takes the POST data.
    # 2. Initializes the serializer_class (UserCreateSerializer) with the data.
    # 3. Calls serializer.is_valid() to run validation.
    # 4. If valid, calls serializer.save() which triggers our custom `create` method.
    # 5. Returns a 201 Created response with the serialized user data (as defined by serializer fields).
    # 6. Returns a 400 Bad Request response if validation fails.


class ProfileImageUploadView(APIView):
    def post(self, request):
        """Get a presigned URL for uploading profile image."""
        try:
            # Generate a unique S3 key for the image
            s3_key = f"users/{request.user.id}/profile.jpg"
            # get the file from the request
            file = request.data.get("image")
            # Check if the file is provided
            if not file:
                return Response(
                    {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
                )
            uploader = S3ImageUploader()
            presigned_url = uploader.upload_image(file, s3_key)
            if presigned_url:
                # Optionally, you can save the image metadata to the user's profile
                user_profile = UserProfile.objects.get(user=request.user)
                user_profile.profile_picture_s3_key = s3_key
                user_profile.save()
                # Return the presigned URL and S3 key
                # in the response
            return Response({"presigned_url": presigned_url, "s3_key": s3_key})
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CoverImageUploadView(APIView):
    def post(self, request):
        """Get a presigned URL for uploading cover image."""
        try:
            # Generate a unique S3 key for the image
            s3_key = f"users/{request.user.id}/cover-image.jpg"
            # get the file from the request
            file = request.data.get("cover-image")
            # Check if the file is provided
            if not file:
                return Response(
                    {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
                )
            uploader = S3ImageUploader()
            presigned_url = uploader.upload_image(file, s3_key)
            if presigned_url:
                # Optionally, you can save the image metadata to the user's profile
                user_profile = UserProfile.objects.get(user=request.user)
                user_profile.cover_photo_s3_key = s3_key
                user_profile.save()
                # Return the presigned URL and S3 key
                # in the response
            return Response({"presigned_url": presigned_url, "s3_key": s3_key})
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserCommunityMembershipListView(generics.ListCreateAPIView):
    """
    View to list all communities a user is a member of and to join new communities.
    """
    serializer_class = UserCommunityMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return all communities the current user is a member of"""
        return UserCommunityMembership.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Join a new community"""
        # Check if the user is already a member of this community
        community = serializer.validated_data['community']
        if UserCommunityMembership.objects.filter(user=self.request.user, community=community).exists():
            raise ValidationError("You are already a member of this community.")
        
        # Determine if this should be the primary community
        is_primary = serializer.validated_data.get('is_primary', False)
        
        # If this is the user's first community, automatically make it primary
        if not UserCommunityMembership.objects.filter(user=self.request.user).exists():
            is_primary = True
            
        serializer.save(user=self.request.user, is_primary=is_primary)


class UserCommunityMembershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, or delete a specific community membership.
    Update can be used to set a community as primary.
    Delete is used to leave a community.
    """
    serializer_class = UserCommunityMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only memberships owned by the current user"""
        return UserCommunityMembership.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Handle leaving a community"""
        membership = self.get_object()
        
        # Check if this is the user's primary community
        if membership.is_primary:
            # Find another community to make primary if possible
            other_membership = UserCommunityMembership.objects.filter(
                user=self.request.user
            ).exclude(id=membership.id).first()
            
            # If user has another community, make it primary
            if other_membership:
                other_membership.is_primary = True
                other_membership.save()
                
                # Update user profile to use this community
                profile, created = UserProfile.objects.get_or_create(user=self.request.user)
                profile.community = other_membership.community
                profile.save(update_fields=['community'])
            else:
                # If no other communities, clear the primary community in user profile
                profile, created = UserProfile.objects.get_or_create(user=self.request.user)
                profile.community = None
                profile.save(update_fields=['community'])
        
        return super().destroy(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        """Handle updating a membership, particularly when setting as primary"""
        is_primary = serializer.validated_data.get('is_primary', False)
        
        # If setting as primary, the save method in the model will handle making other memberships non-primary
        serializer.save(is_primary=is_primary)