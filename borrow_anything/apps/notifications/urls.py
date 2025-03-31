# apps/notifications/urls.py

from django.urls import path
from . import views # Import views from the current directory

# Define URL patterns manually, mapping methods to NotificationViewSet actions
urlpatterns = [
    # Map GET requests to '/notifications/' -> list action
    path('notifications/',
         views.NotificationViewSet.as_view({
             'get': 'list',
         }),
         name='notification-list'),

    # Map PATCH and DELETE requests to '/notifications/<pk>/'
    path('notifications/<int:pk>/',
         views.NotificationViewSet.as_view({
             'patch': 'partial_update', # For marking as read (updates 'is_read')
             'delete': 'destroy',       # For deleting a notification
             # GET (retrieve) is not included as we don't have RetrieveModelMixin
         }),
         name='notification-detail'), # Name covers both PATCH and DELETE here

    # Map POST requests to '/notifications/mark-all-read/' -> custom action
    path('notifications/mark-all-read/',
         views.NotificationViewSet.as_view({
             'post': 'mark_all_read',
         }),
         name='notification-mark-all-read'),
]
