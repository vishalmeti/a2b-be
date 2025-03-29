# apps/communities/urls.py

from django.urls import path
from . import views # Import views from the current directory

# Define URL patterns manually
urlpatterns = [
    # Map GET requests on '/communities/' to the 'list' method of CommunityViewSet
    path('communities/',
         views.CommunityViewSet.as_view({'get': 'list'}),
         name='community-list'),

    # Map GET requests on '/communities/<pk>/' to the 'retrieve' method of CommunityViewSet
    path('communities/<int:pk>/',
         views.CommunityViewSet.as_view({'get': 'retrieve'}),
         name='community-detail'),

    # Keep the separate path for creating suggestions
    path('suggestions/',
         views.CommunitySuggestionCreateView.as_view(),
         name='community-suggestion-create'),
]