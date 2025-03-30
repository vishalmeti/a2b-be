# apps/items/urls.py

from django.urls import path
from . import views # Import views from the current directory

# Define URL patterns manually, mapping methods to ViewSet actions
urlpatterns = [
    # Categories (Read-Only)
    path('categories/',
         views.CategoryViewSet.as_view({'get': 'list'}), # Map GET to .list() method
         name='category-list'),
    path('categories/<int:pk>/',
         views.CategoryViewSet.as_view({'get': 'retrieve'}), # Map GET to .retrieve() method
         name='category-detail'),

    # Items (Full CRUD)
    path('items/',
         views.ItemViewSet.as_view({
             'get': 'list', # Map GET to .list() method
             'post': 'create' # Map POST to .create() method
         }),
         name='item-list'),
    path('items/<int:pk>/',
         views.ItemViewSet.as_view({
             'get': 'retrieve', # Map GET to .retrieve() method
             'put': 'update', # Map PUT to .update() method
             'patch': 'partial_update', # Map PATCH to .partial_update() method
             'delete': 'destroy' # Map DELETE to .destroy() method
         }),
         name='item-detail'),

    path('items/<int:item_pk>/images/',
         views.ItemImageUploadView.as_view(),
         name='item-image-upload'),
]