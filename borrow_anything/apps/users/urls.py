# apps/users/urls.py

from django.urls import path
from . import views

app_name = 'users' # Optional namespace

urlpatterns = [
    # Maps GET/PUT/PATCH requests on 'me/' to the ManageUserView
    path("me/", views.ManageUserView.as_view(), name="me"),
    path("register/", views.UserCreateView.as_view(), name="register"),
    path(
        "profile-image/", views.ProfileImageUploadView.as_view(), name="profile-image"
    ),
    # Add other user-related URLs later (e.g., signup, password change)
]
