# filepath: d:\Github\tennis_community_manager\community\permissions.py
from rest_framework import permissions
from .models import CommunityUsers
from users.models import UserProfile

class IsCommunityMember(permissions.BasePermission):
    """
    Allows access only to members of the community.
    Assumes the view has a 'pk' kwarg for the community ID.
    """
    message = "You must be a member of this community to perform this action."

    def has_permission(self, request, view):
        community_id = view.kwargs.get('pk')
        if not community_id:
            return False # Cannot check without community ID

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            return CommunityUsers.objects.filter(
                community_id=community_id,
                user=user_profile
            ).exists()
        except UserProfile.DoesNotExist:
            return False # User profile doesn't exist

class IsCommunityAdminOrModerator(permissions.BasePermission):
    """
    Allows access only to admins or moderators of the community.
    Assumes the view has a 'pk' kwarg for the community ID.
    """
    message = "You must be an admin or moderator of this community."

    def has_permission(self, request, view):
        community_id = view.kwargs.get('pk')
        if not community_id:
            return False

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            return CommunityUsers.objects.filter(
                community_id=community_id,
                user=user_profile,
                role__in=['admin', 'moderator','owner']
            ).exists()
        except UserProfile.DoesNotExist:
            return False

class IsCommunityAdmin(permissions.BasePermission):
    """
    Allows access only to admins of the community.
    Assumes the view has a 'pk' kwarg for the community ID.
    """
    message = "You must be an admin of this community."

    def has_permission(self, request, view):
        community_id = view.kwargs.get('pk')
        if not community_id:
            return False

        try:
            user_profile = UserProfile.objects.get(user=request.user)
            return CommunityUsers.objects.filter(
                community_id=community_id,
                user=user_profile,
                role__in=['admin', 'owner']
            ).exists()
        except UserProfile.DoesNotExist:
            return False