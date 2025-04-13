# Create matches/permissions.py
from rest_framework import permissions
from .models import Match
from users.models import UserProfile
from community.models import CommunityUsers

class IsPlayerInMatchOrCommunityAdmin(permissions.BasePermission):
    message = "Only players in the match or community admins can perform this action."

    def has_object_permission(self, request, view, obj: Match):
        # Check if user is one of the players
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            if user_profile in [obj.home1, obj.home2, obj.away1, obj.away2]:
                return True
        except UserProfile.DoesNotExist:
            pass # Continue to check admin status

        # Check if user is admin/mod of the community (if match belongs to one)
        if obj.community_id:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                return CommunityUsers.objects.filter(
                    community=obj.community_id,
                    user=user_profile,
                    role__in=['admin', 'moderator', 'owner']
                ).exists()
            except UserProfile.DoesNotExist:
                return False
        
        return False # Not a player and not a community admin/mod