# apps/transactions/urls.py

from django.urls import path
from . import views # Import views from the current directory

# Define URL patterns manually, mapping methods to ViewSet actions
urlpatterns = [
    # Map requests to '/requests/'
    path('requests/',
         views.BorrowingRequestViewSet.as_view({
             'get': 'list',     # GET requests call the .list() method
             'post': 'create'   # POST requests call the .create() method
         }),
         name='request-list'), # Name for reversing URLs

    # Map requests to '/requests/<pk>/'
    path('requests/<int:pk>/',
         views.BorrowingRequestViewSet.as_view({
             'get': 'retrieve', # GET requests call the .retrieve() method
             # --- Add mappings for update/delete later when implemented ---
             # 'put': 'update',
             # 'patch': 'partial_update',
             # 'delete': 'destroy',
         }),
         name='request-detail'), # Name for reversing URLs

    # --- Add paths for custom actions later ---
    # Example: path('requests/<int:pk>/accept/', views.BorrowingRequestViewSet.as_view({'patch': 'accept'}), name='request-accept'),
]