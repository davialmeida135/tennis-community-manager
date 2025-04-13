from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Community, CommunityUsers
from users.models import UserProfile
from .serializers import CommunitySerializer, CommunityUsersSerializer
from tournament.serializers import TournamentSerializer
from tournament.models import Tournament
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from .permissions import IsCommunityAdminOrModerator, IsCommunityAdmin, IsCommunityMember
from django.shortcuts import get_object_or_404

User = get_user_model()


class CommunityViewSet(viewsets.ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    permission_classes = [IsAuthenticated]
    @action(detail=True, methods=["post"], permission_classes=[IsCommunityAdminOrModerator])
    def invite_user(self, request, pk=None):
        """Invites a user to join the community."""
        community = self.get_object()
        user_id_to_invite = request.data.get("id")

        if not user_id_to_invite:
            return Response({"error": "User ID must be provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Use UserProfile directly since that's the FK
            user_profile_to_invite = UserProfile.objects.get(id=user_id_to_invite)
        except UserProfile.DoesNotExist:
            return Response({"error": "User to invite does not exist."}, status=status.HTTP_404_NOT_FOUND)

        # Check if relationship already exists (pending or active)
        existing_relation, created = CommunityUsers.objects.get_or_create(
            community=community,
            user=user_profile_to_invite,
            defaults={'role': 'pending_invitation'} # Default if creating new
        )

        if not created:
            # Relationship exists, check its status
            if existing_relation.role not in ['pending_invitation', 'pending_request']:
                 return Response({"error": "User is already a member or has a pending request."}, status=status.HTTP_400_BAD_REQUEST)
            # If it was a pending_request, maybe upgrade to pending_invitation? Or just inform?
            # For simplicity, let's just say it's already pending if not created.
            # If it already was pending_invitation, maybe resend? For now, just return success.
            existing_relation.role = 'pending_invitation' # Ensure it's set/reset to invitation
            existing_relation.save()

        serializer = CommunityUsersSerializer(existing_relation)
        return Response({"message": "Invitation sent successfully.", "details": serializer.data}, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    # --- Join Request Logic ---
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated]) # Any logged-in user can request
    def request_join(self, request, pk=None):
        """Requests to join a community."""
        community = self.get_object()
        requesting_user_profile = get_object_or_404(UserProfile, user=request.user)

        # Check if community is private - might disallow requests entirely?
        # if community.is_private:
        #     return Response({"error": "This community is private and does not accept join requests."}, status=status.HTTP_403_FORBIDDEN)

        existing_relation, created = CommunityUsers.objects.get_or_create(
            community=community,
            user=requesting_user_profile,
            defaults={'role': 'pending_request'}
        )

        if not created:
            return Response({"error": f"You already have a status ({existing_relation.get_role_display()}) with this community."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CommunityUsersSerializer(existing_relation)
        return Response({"message": "Join request sent successfully.", "details": serializer.data}, status=status.HTTP_201_CREATED)

    # --- Manage Join Requests ---
    @action(detail=True, methods=["get"], permission_classes=[IsCommunityAdminOrModerator], url_path='pending-requests')
    def list_pending_requests(self, request, pk=None):
        """Lists users who have requested to join."""
        community = self.get_object()
        pending_requests = CommunityUsers.objects.filter(community=community, role='pending_request')
        serializer = CommunityUsersSerializer(pending_requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsCommunityAdminOrModerator], url_path='pending-requests/(?P<cu_id>[^/.]+)/accept')
    def accept_request(self, request, pk=None, cu_id=None):
        """Accepts a user's request to join."""
        community = self.get_object() # Ensures admin has access to this community
        membership_request = get_object_or_404(CommunityUsers, id=cu_id, community=community, role='pending_request')

        membership_request.role = 'member' # Or maybe default role?
        membership_request.save()

        serializer = CommunityUsersSerializer(membership_request)
        return Response({"message": "Join request accepted.", "details": serializer.data})

    @action(detail=True, methods=["post"], permission_classes=[IsCommunityAdminOrModerator], url_path='pending-requests/(?P<cu_id>[^/.]+)/reject')
    def reject_request(self, request, pk=None, cu_id=None):
        """Rejects a user's request to join."""
        community = self.get_object()
        membership_request = get_object_or_404(CommunityUsers, id=cu_id, community=community, role='pending_request')

        membership_request.delete() # Remove the request entirely

        return Response({"message": "Join request rejected."}, status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=["post"], permission_classes=[IsCommunityAdminOrModerator])
    def add_user(self, request, pk=None): # pk é o ID da comunidade
        """
        Adiciona um usuário pré-existente à comunidade.
        """
        community = self.get_object()
        user_id = request.data.get("id")

        try:
            # Verifica se o usuário existe
            user = User.objects.get(pk=user_id)
            user_profile = UserProfile.objects.get(user=user)
        except User.DoesNotExist:
            return Response(
                {"error": "Usuário não existe."},
                status=status.HTTP_400_BAD_REQUEST
            ) 

        # Se necessário, você pode verificar se o usuário já pertence à comunidade
        membership = CommunityUsers.objects.filter(
            community=community,
            user=user_profile
        )
        if membership.exists():
            return Response(
                {"error": "Usuário já pertence à comunidade."},
                status=status.HTTP_400_BAD_REQUEST
            )
        CommunityUsers.objects.create(
            community=community,
            user=user_profile,  # associa o usuário existente
        )
        return Response(
            {"message": "Usuário adicionado com sucesso"},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=["post"], permission_classes=[IsCommunityAdminOrModerator])
    def remove_user(self, request, pk=None): # pk é o ID da comunidade
        """
        Remove um usuário da comunidade.
        """
        community = self.get_object()
        user_id = request.data.get("id")

        request_user = request.user.first_name
        #print(f"{request_user} is trying to remove user {user_id} from community {pk}")

        try:
            # Verifica se o usuário existe
            user = User.objects.get(pk=user_id)
            user_profile = UserProfile.objects.get(user=user)
        except User.DoesNotExist:
            return Response(
                {"error": "Usuário não existe."},
                status=status.HTTP_400_BAD_REQUEST
            ) 

        # Se necessário, você pode verificar se o usuário pertence à comunidade
        membership = CommunityUsers.objects.filter(
            community=community,
            user=user_profile
        )
        if not membership.exists():
            return Response(
                {"error": "Usuário não pertence à comunidade."},
                status=status.HTTP_400_BAD_REQUEST
            )
        membership.delete()

        return Response(
            {"message": f"Usuário removido da comunidade {pk} com sucesso"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=["post"])
    def edit_user_permissions(self, request, pk=None,permission_classes=[IsCommunityAdmin]):
        """
        Edita as permissões de um usuário na comunidade.
        """
        community = self.get_object()
        user_id = request.data.get("id")
        role = request.data.get("role")

        try:
            # Verifica se o usuário existe
            user = User.objects.get(pk=user_id)
            user_profile = UserProfile.objects.get(user=user)
        except User.DoesNotExist:
            return Response(
                {"error": "Usuário não existe."},
                status=status.HTTP_400_BAD_REQUEST
            ) 

        # Se necessário, você pode verificar se o usuário pertence à comunidade
        membership = CommunityUsers.objects.filter(
            community=community,
            user=user_profile
        )
        if not membership.exists():
            return Response(
                {"error": "Usuário não pertence à comunidade."},
                status=status.HTTP_400_BAD_REQUEST
            )
        membership.update(role=role)

        return Response(
            {"message": f"Permissões do usuário {user_id} atualizadas com sucesso"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=["get"])
    def users(self, request, pk=None):
        """Return all users for this community."""
        community = self.get_object()
        users = CommunityUsers.objects.filter(community_id=community)
        serializer = CommunityUsersSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["get"])
    def tournaments(self, request, pk=None):
        """Return all tournaments for this community."""
        community = self.get_object()
        tournaments = Tournament.objects.filter(community_id=community)
        serializer = TournamentSerializer(tournaments, many=True)
        return Response(serializer.data)
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['update', 'partial_update', 'destroy']:
            # Example: Only admins can modify/delete a community
            self.permission_classes = [IsCommunityAdmin]
        elif self.action == 'retrieve':
            # Example: Any authenticated user can view details (or use IsCommunityMember)
            self.permission_classes = [IsAuthenticated]
        elif self.action == 'list':
             # Example: Any authenticated user can list communities
            self.permission_classes = [IsAuthenticated]
        # For 'create', IsAuthenticated is applied by default from settings
        # For custom actions, permissions are set via the decorator
        return super().get_permissions()
    
