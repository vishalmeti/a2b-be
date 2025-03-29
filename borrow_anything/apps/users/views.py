from django.shortcuts import render

# Create your views here.
# apps/users/views.py

from rest_framework import generics, permissions
from .models import UserProfile
from .serializers import UserProfileSerializer  # Make sure this serializer is defined
from django.contrib.auth import get_user_model
from .serializers import UserCreateSerializer

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
