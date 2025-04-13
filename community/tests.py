from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from community.models import Community, CommunityUsers
from users.models import UserProfile
# Remove Token import
# from rest_framework.authtoken.models import Token

User = get_user_model()

# --- Model Tests (Remain Largely Unchanged) ---
class CommunityModelTests(TestCase):
    def setUp(self):
        # Create a user and profile for testing
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            forehand='Right',
            backhand='One-handed'
        )

        # Create a community
        self.community = Community.objects.create(
            name='Tennis Club',
            description='A community for tennis enthusiasts'
        )

    def test_community_creation(self):
        """Test that a community can be created correctly"""
        self.assertEqual(self.community.name, 'Tennis Club')
        self.assertEqual(self.community.description, 'A community for tennis enthusiasts')

    def test_community_user_relationship(self):
        """Test that users can be added to a community with roles"""
        # Add user to community as admin
        community_user = CommunityUsers.objects.create(
            user=self.profile,
            community=self.community,
            role='admin' # Use lowercase role names as defined in models
        )

        self.assertEqual(community_user.community, self.community)
        self.assertEqual(community_user.user, self.profile)
        self.assertEqual(community_user.role, 'admin')
        self.assertEqual(str(community_user), f"{self.user.username} in {self.community.name} (admin)") # Test __str__

    def test_community_user_roles(self):
        """Test different roles can be assigned"""
        CommunityUsers.objects.create(user=self.profile, community=self.community, role='member')
        self.assertTrue(CommunityUsers.objects.filter(user=self.profile, community=self.community, role='member').exists())

    def test_unique_community_user(self):
        """Test that a user can only have one role per community"""
        CommunityUsers.objects.create(user=self.profile, community=self.community, role='member')
        with self.assertRaises(Exception): # Should raise IntegrityError or similar due to unique_together
            CommunityUsers.objects.create(user=self.profile, community=self.community, role='admin')


# --- API Tests (Rewritten for JWT and Permissions) ---
class CommunityAPITests(APITestCase):
    def setUp(self):
        # Create users with different roles in mind
        self.owner_user = User.objects.create_user(username='owner', password='password')
        self.admin_user = User.objects.create_user(username='admin', password='password')
        self.mod_user = User.objects.create_user(username='moderator', password='password')
        self.member_user = User.objects.create_user(username='member', password='password')
        self.non_member_user = User.objects.create_user(username='nonmember', password='password')
        self.pending_user = User.objects.create_user(username='pending', password='password') # User who will request join
        self.invited_user = User.objects.create_user(username='invited', password='password') # User who will be invited

        # Create profiles
        self.owner_profile = UserProfile.objects.create(user=self.owner_user)
        self.admin_profile = UserProfile.objects.create(user=self.admin_user)
        self.mod_profile = UserProfile.objects.create(user=self.mod_user)
        self.member_profile = UserProfile.objects.create(user=self.member_user)
        self.non_member_profile = UserProfile.objects.create(user=self.non_member_user)
        self.pending_profile = UserProfile.objects.create(user=self.pending_user)
        self.invited_profile = UserProfile.objects.create(user=self.invited_user)

        # Create a community
        self.community = Community.objects.create(name='Test Community', description='For API tests')

        # Assign roles within the community
        CommunityUsers.objects.create(community=self.community, user=self.owner_profile, role='owner')
        CommunityUsers.objects.create(community=self.community, user=self.admin_profile, role='admin')
        CommunityUsers.objects.create(community=self.community, user=self.mod_profile, role='moderator')
        CommunityUsers.objects.create(community=self.community, user=self.member_profile, role='member')
        # non_member_profile, pending_profile, invited_profile are not initially linked

        # Store credentials
        self.owner_creds = {'username': 'owner', 'password': 'password'}
        self.admin_creds = {'username': 'admin', 'password': 'password'}
        self.mod_creds = {'username': 'moderator', 'password': 'password'}
        self.member_creds = {'username': 'member', 'password': 'password'}
        self.non_member_creds = {'username': 'nonmember', 'password': 'password'}
        self.pending_creds = {'username': 'pending', 'password': 'password'}
        self.invited_creds = {'username': 'invited', 'password': 'password'}

    # --- Helper Methods for Auth ---
    def _get_jwt_token(self, credentials):
        """Helper to obtain JWT access token."""
        response = self.client.post('/api/token/', credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to get token: {response.data}")
        self.assertIn('access', response.data)
        return response.data['access']

    def _authenticate_user(self, credentials):
        """Helper to authenticate the client with JWT."""
        token = self._get_jwt_token(credentials)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # --- CRUD Tests ---
    def test_create_community_authenticated(self):
        """Test that an authenticated user can create a community (becomes owner)."""
        self._authenticate_user(self.owner_creds) # Any authenticated user can create

        data = {'name': 'New Tennis Club', 'description': 'A brand new community'}
        response = self.client.post('/api/communities/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Tennis Club')

        # Check if community was created
        community = Community.objects.get(name='New Tennis Club')
        self.assertEqual(community.description, 'A brand new community')

        # Check if the creator was added as owner
        community_user = CommunityUsers.objects.get(community=community, user=self.owner_profile)
        self.assertEqual(community_user.role, 'owner') # Check if create logic sets owner correctly

    def test_create_community_unauthenticated(self):
        """Test that unauthenticated users can't create communities."""
        data = {'name': 'Unauth Club', 'description': 'Should fail'}
        response = self.client.post('/api/communities/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_communities_authenticated(self):
        """Test listing communities requires authentication."""
        self._authenticate_user(self.member_creds)
        response = self.client.get('/api/communities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if the created community is in the list
        self.assertTrue(any(c['name'] == self.community.name for c in response.data))

    def test_list_communities_unauthenticated(self):
        """Test listing communities fails if unauthenticated."""
        response = self.client.get('/api/communities/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_community_authenticated(self):
        """Test retrieving a specific community requires authentication."""
        self._authenticate_user(self.member_creds)
        url = f'/api/communities/{self.community.community_id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.community.name)

    def test_retrieve_community_unauthenticated(self):
        """Test retrieving a specific community fails if unauthenticated."""
        url = f'/api/communities/{self.community.community_id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_community_permission(self):
        """Test only admins/owners can update community details."""
        url = f'/api/communities/{self.community.community_id}/'
        data = {'description': 'Updated Description'}

        # Try as member (should fail)
        self._authenticate_user(self.member_creds)
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Assuming IsCommunityAdmin permission

        # Try as moderator (should fail)
        self._authenticate_user(self.mod_creds)
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Assuming IsCommunityAdmin permission

        # Try as admin (should succeed)
        self._authenticate_user(self.admin_creds)
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated Description')
        self.community.refresh_from_db()
        self.assertEqual(self.community.description, 'Updated Description')

        # Try as owner (should succeed)
        self._authenticate_user(self.owner_creds)
        data = {'description': 'Owner Update'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Owner Update')

    def test_delete_community_permission(self):
        """Test only admins/owners can delete a community."""
        url = f'/api/communities/{self.community.community_id}/'

        # Try as member (should fail)
        self._authenticate_user(self.member_creds)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try as moderator (should fail)
        self._authenticate_user(self.mod_creds)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try as admin (should succeed)
        self._authenticate_user(self.admin_creds)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Community.objects.filter(pk=self.community.community_id).exists())

        # Recreate for owner test
        self.community = Community.objects.create(name='Test Community 2')
        CommunityUsers.objects.create(community=self.community, user=self.owner_profile, role='owner')
        url = f'/api/communities/{self.community.community_id}/'

        # Try as owner (should succeed)
        self._authenticate_user(self.owner_creds)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Community.objects.filter(pk=self.community.community_id).exists())


    # --- Member Management Tests ---

    def test_list_community_users_permission(self):
        """Test only members can list users of a community."""
        url = f'/api/communities/{self.community.community_id}/users/'

        # Try as non-member (should fail)
        self._authenticate_user(self.non_member_creds)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Assuming IsCommunityMember

        # Try as member (should succeed)
        self._authenticate_user(self.member_creds)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if expected members are present (owner, admin, mod, member)
        self.assertEqual(len(response.data), 4)
        usernames = [u['user']['user']['username'] for u in response.data]
        self.assertIn('owner', usernames)
        self.assertIn('admin', usernames)
        self.assertIn('moderator', usernames)
        self.assertIn('member', usernames)

    def test_add_user_permission(self):
        """Test only admins/mods/owners can add users directly."""
        url = f'/api/communities/{self.community.community_id}/add_user/'
        data = {'id': self.non_member_profile.id, 'role': 'member'}
        print(self.non_member_profile)

        # Try as member (should fail)
        self._authenticate_user(self.member_creds)
        response = self.client.post(url, data, format='json')
        print(response)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Assuming IsCommunityAdminOrModerator

        # Try as moderator (should succeed)
        self._authenticate_user(self.mod_creds)
        response = self.client.post(url, data, format='json')
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CommunityUsers.objects.filter(community=self.community, user=self.non_member_profile, role='member').exists())
        CommunityUsers.objects.get(community=self.community, user=self.non_member_profile).delete() # Clean up for next test

        # Try as admin (should succeed)
        self._authenticate_user(self.admin_creds)
        response = self.client.post(url, data, format='json')
        print(response)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CommunityUsers.objects.filter(community=self.community, user=self.non_member_profile, role='member').exists())

    def test_remove_user_permission(self):
        """Test only admins/mods/owners can remove users."""
        # Use the member added in setup
        url = f'/api/communities/{self.community.community_id}/remove_user/'
        data = {'id': self.member_profile.id}

        # Try as member (should fail)
        self._authenticate_user(self.member_creds)
        response = self.client.post(url, data, format='json') # Assuming remove_user is POST
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try as moderator (should succeed)
        self._authenticate_user(self.mod_creds)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Or 204 if no content
        self.assertFalse(CommunityUsers.objects.filter(community=self.community, user=self.member_profile).exists())

        # Re-add member for admin test
        CommunityUsers.objects.create(community=self.community, user=self.member_profile, role='member')

        # Try as admin (should succeed)
        self._authenticate_user(self.admin_creds)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Or 204
        self.assertFalse(CommunityUsers.objects.filter(community=self.community, user=self.member_profile).exists())

    # --- Invite/Request Logic Tests ---

    def test_invite_user_permission(self):
        """Test only admins/mods/owners can invite users."""
        url = f'/api/communities/{self.community.community_id}/invite_user/'
        data = {'id': self.invited_profile.id}

        # Try as member (should fail)
        self._authenticate_user(self.member_creds)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try as moderator (should succeed)
        self._authenticate_user(self.mod_creds)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CommunityUsers.objects.filter(community=self.community, user=self.invited_profile, role='pending_invitation').exists())
        CommunityUsers.objects.get(community=self.community, user=self.invited_profile).delete() # Clean up

        # Try as admin (should succeed)
        self._authenticate_user(self.admin_creds)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CommunityUsers.objects.filter(community=self.community, user=self.invited_profile, role='pending_invitation').exists())

    def test_request_join_permission(self):
        """Test any authenticated user can request to join."""
        url = f'/api/communities/{self.community.community_id}/request_join/'

        # Try as non-member (should succeed)
        self._authenticate_user(self.pending_creds)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CommunityUsers.objects.filter(community=self.community, user=self.pending_profile, role='pending_request').exists())

        # Try again (should fail - already pending)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try as existing member (should fail)
        self._authenticate_user(self.member_creds)
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_pending_requests_permission(self):
        """Test only admins/mods/owners can list pending requests."""
        # Create a pending request first
        CommunityUsers.objects.create(community=self.community, user=self.pending_profile, role='pending_request')
        url = f'/api/communities/{self.community.community_id}/pending-requests/'

        # Try as member (should fail)
        self._authenticate_user(self.member_creds)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try as moderator (should succeed)
        self._authenticate_user(self.mod_creds)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user']['user']['username'], 'pending')

    def test_accept_reject_request_permission(self):
        """Test only admins/mods/owners can accept/reject requests."""
        pending_request = CommunityUsers.objects.create(community=self.community, user=self.pending_profile, role='pending_request')
        accept_url = f'/api/communities/{self.community.community_id}/pending-requests/{pending_request.id}/accept/'
        reject_url = f'/api/communities/{self.community.community_id}/pending-requests/{pending_request.id}/reject/'

        # Try accept as member (should fail)
        self._authenticate_user(self.member_creds)
        response = self.client.post(accept_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try accept as moderator (should succeed)
        self._authenticate_user(self.mod_creds)
        response = self.client.post(accept_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending_request.refresh_from_db()
        self.assertEqual(pending_request.role, 'member')

        # Reset for reject test
        pending_request.role = 'pending_request'
        pending_request.save()

        # Try reject as member (should fail)
        self._authenticate_user(self.member_creds)
        response = self.client.post(reject_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Try reject as admin (should succeed)
        self._authenticate_user(self.admin_creds)
        response = self.client.post(reject_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CommunityUsers.objects.filter(id=pending_request.id).exists())

    # def test_list_accept_reject_invitation(self):
    #     """Test user can list, accept, and reject their own invitations."""
    #     # Admin invites the 'invited_user'
    #     self._authenticate_user(self.admin_creds)
    #     invite_url = f'/api/communities/{self.community.community_id}/invite_user/'
    #     invite_data = {'id': self.invited_profile.id}
    #     response = self.client.post(invite_url, invite_data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     invitation = CommunityUsers.objects.get(community=self.community, user=self.invited_profile)

    #     # Authenticate as the invited user
    #     self._authenticate_user(self.invited_creds)

    #     # List invitations
    #     list_url = '/api/users/me/invitations/'
    #     response = self.client.get(list_url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(response.data), 1)
    #     self.assertEqual(response.data[0]['id'], invitation.id)
    #     self.assertEqual(response.data[0]['community'], self.community.community_id)

    #     # Accept invitation
    #     accept_url = f'/api/users/me/invitations/{invitation.id}/accept/'
    #     response = self.client.post(accept_url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     invitation.refresh_from_db()
    #     self.assertEqual(invitation.role, 'member')

    #     # Reset for reject test
    #     invitation.role = 'pending_invitation'
    #     invitation.save()

    #     # Reject invitation
    #     reject_url = f'/api/users/me/invitations/{invitation.id}/reject/'
    #     response = self.client.post(reject_url)
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    #     self.assertFalse(CommunityUsers.objects.filter(id=invitation.id).exists())

    def test_accept_reject_other_user_invitation(self):
        """Test user cannot accept/reject another user's invitation."""
        # Admin invites the 'invited_user'
        self._authenticate_user(self.admin_creds)
        invite_url = f'/api/communities/{self.community.community_id}/invite_user/'
        invite_data = {'id': self.invited_profile.id}
        response = self.client.post(invite_url, invite_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invitation = CommunityUsers.objects.get(community=self.community, user=self.invited_profile)

        # Authenticate as a different user (non_member)
        self._authenticate_user(self.non_member_creds)

        # Try to accept the invitation meant for 'invited_user'
        accept_url = f'/api/users/me/invitations/{invitation.id}/accept/'
        response = self.client.post(accept_url)
        # Expect 404 because the query filters by request.user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Try to reject
        reject_url = f'/api/users/me/invitations/{invitation.id}/reject/'
        response = self.client.post(reject_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify invitation is unchanged
        invitation.refresh_from_db()
        self.assertEqual(invitation.role, 'pending_invitation')
