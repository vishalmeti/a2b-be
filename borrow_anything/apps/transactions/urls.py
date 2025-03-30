# apps/transactions/urls.py

from django.urls import path
from . import views # Import views from the current directory

# Define URL patterns manually, mapping methods to ViewSet actions
urlpatterns = [
    # Map requests to '/requests/'
    path(
        "requests/",
        views.BorrowingRequestViewSet.as_view(
            {
                "get": "list",  # GET requests call the .list() method
                "post": "create",  # POST requests call the .create() method
            }
        ),
        name="request-list",
    ),  # Name for reversing URLs
    # Map requests to '/requests/<pk>/'
    path(
        "requests/<int:pk>/",
        views.BorrowingRequestViewSet.as_view(
            {
                "get": "retrieve",  # GET requests call the .retrieve() method
                # --- Add mappings for update/delete later when implemented ---
                # 'put': 'update',
                # 'patch': 'partial_update',
                # 'delete': 'destroy',
            }
        ),
        name="request-detail",
    ),  # Name for reversing URLs
    # --- Add Paths for Custom Actions ---
    path(
        "requests/<int:pk>/accept/",
        views.BorrowingRequestViewSet.as_view(
            {"patch": "accept"}  # Map PATCH method to 'accept' action
        ),
        name="request-accept",
    ),
    path(
        "requests/<int:pk>/decline/",
        views.BorrowingRequestViewSet.as_view(
            {"patch": "decline"}  # Map PATCH method to 'decline' action
        ),
        name="request-decline",
    ),
    # --- Add Borrower Actions URLs ---
    path(
        "requests/<int:pk>/cancel/",
        views.BorrowingRequestViewSet.as_view({"patch": "cancel"}),
        name="request-cancel",
    ),
    path(
        "requests/<int:pk>/confirm-pickup/",
        views.BorrowingRequestViewSet.as_view({"patch": "confirm_pickup"}),
        name="request-confirm-pickup",
    ),
]
