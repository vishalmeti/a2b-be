# apps/communities/views.py

from rest_framework import viewsets, permissions, generics, filters, mixins

# We need mixins for list and retrieve actions with GenericViewSet
from .models import Community, CommunitySuggestion
from .serializers import CommunitySerializer, CommunitySuggestionSerializer


class CommunityViewSet(
    mixins.ListModelMixin,  # Provides the .list() action handler
    mixins.RetrieveModelMixin,  # Provides the .retrieve() action handler
    viewsets.GenericViewSet,
):  # Provides base functionality like get_queryset, get_object etc.
    """
    API endpoint for listing and retrieving approved Communities using GenericViewSet.

    Inherits from GenericViewSet and includes List/Retrieve mixins.
    Filtering by 'pincode', 'city', and 'search' query parameters is supported.
    """

    serializer_class = CommunitySerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]  # Only authenticated users can view
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "pincode", "city"]

    def get_queryset(self):
        """
        Only list communities that are approved and active.
        Applies query parameter filtering for pincode and city.
        """
        queryset = Community.objects.filter(is_approved=True, is_active=True)

        # Filter by pincode if provided in query params
        pincode = self.request.query_params.get("pincode")
        if pincode:
            queryset = queryset.filter(pincode=pincode)

        # Filter by city if provided in query params
        city = self.request.query_params.get("city")
        if city:
            # Use case-insensitive filtering for city name
            queryset = queryset.filter(city__iexact=city)

        return queryset

    # NOTE: We don't need to explicitly write list() or retrieve() methods here
    # because ListModelMixin and RetrieveModelMixin provide them.
    # If we wanted custom behavior, we *could* override them.


# --- Keep the CommunitySuggestionCreateView as it is ---
# (It handles a different model and only needs 'create')
class CommunitySuggestionCreateView(generics.CreateAPIView):
    """
    API endpoint for creating Community Suggestions.
    Handles POST requests to /api/v1/suggestions/ (URL defined separately)
    """

    queryset = CommunitySuggestion.objects.all()
    serializer_class = CommunitySuggestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Automatically set the 'suggested_by' field"""
        serializer.save(suggested_by=self.request.user)
