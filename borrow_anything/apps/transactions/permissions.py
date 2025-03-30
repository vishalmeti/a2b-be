# apps/transactions/permissions.py

from rest_framework import permissions

class IsReviewParticipant(permissions.BasePermission):
    """
    Object-level permission to only allow borrower or lender of the associated
    borrowing request to view/edit the review.
    """
    def has_object_permission(self, request, view, obj):
        # obj here is the Review instance
        user_profile = getattr(request.user, 'profile', None)

        # Check if the user has a profile and if that profile matches
        # either the borrower or the lender of the linked borrowing request.
        # Ensure borrowing_request relation is loaded.
        if hasattr(obj, 'borrowing_request'):
            return user_profile and \
                   (obj.borrowing_request.borrower_profile == user_profile or \
                    obj.borrowing_request.lender_profile == user_profile)
        return False # Cannot determine participant if request is missing