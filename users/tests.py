from rest_framework.test import APITestCase
from rest_framework import status
from users.models import UserProfile
from django.contrib.auth import get_user_model
# Remove Token import if not used elsewhere
# from rest_framework.authtoken.models import Token

User = get_user_model()

class UserAuthPermissionTests(APITestCase):

    def setUp(self):
        # User 1 (for most tests)
        self.user1_data = {
            "username": "testuser1",
            "email": "testuser1@example.com",
            "password": "securepassword123",
        }
        self.user1 = User.objects.create_user(**self.user1_data)
        self.profile1 = UserProfile.objects.create(
            user=self.user1, forehand="Right", backhand="One Handed"
        )

        # User 2 (for permission checks)
        self.user2_data = {
            "username": "testuser2",
            "email": "testuser2@example.com",
            "password": "securepassword456",
        }
        self.user2 = User.objects.create_user(**self.user2_data)
        self.profile2 = UserProfile.objects.create(
            user=self.user2, forehand="Left", backhand="Two Handed"
        )

        # Store login credentials for convenience
        self.login1_credentials = {
            "username": self.user1_data["username"],
            "password": self.user1_data["password"],
        }
        self.login2_credentials = {
            "username": self.user2_data["username"],
            "password": self.user2_data["password"],
        }

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

    # --- Authentication Tests ---

    def test_login_success(self):
        """Test successful login obtains JWT access and refresh tokens."""
        response = self.client.post('/api/token/', self.login1_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_fail_invalid_username(self):
        """Test login with non-existent username fails."""
        invalid_credentials = self.login1_credentials.copy()
        invalid_credentials["username"] = "nonexistentuser"
        response = self.client.post('/api/token/', invalid_credentials, format='json')
        # simplejwt returns 401 for invalid credentials
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_fail_invalid_password(self):
        """Test login with incorrect password fails."""
        invalid_credentials = self.login1_credentials.copy()
        invalid_credentials["password"] = "wrongpassword"
        response = self.client.post('/api/token/', invalid_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Permission Tests ---

    def test_list_users_unauthenticated(self):
        """Test listing users requires authentication."""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_users_authenticated(self):
        """Test authenticated users can list users."""
        self._authenticate_user(self.login1_credentials)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if both users are listed (adjust if pagination is enabled)
        self.assertTrue(any(u['username'] == self.user1_data['username'] for u in response.data))
        self.assertTrue(any(u['username'] == self.user2_data['username'] for u in response.data))


    def test_retrieve_user_authenticated(self):
        """Test authenticated users can retrieve user details."""
        self._authenticate_user(self.login1_credentials)
        response = self.client.get(f'/api/users/{self.user2.id}/') # Retrieve other user
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user2_data['username'])

    def test_retrieve_user_unauthenticated(self):
        """Test retrieving user details requires authentication."""
        response = self.client.get(f'/api/users/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_unauthenticated(self):
        """Test creating a user does NOT require authentication (as per get_permissions)."""
        new_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            # Profile data might be handled by serializer or signals
        }
        response = self.client.post('/api/users/', new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], "newuser")

    def test_update_own_user_authenticated(self):
        """Test authenticated user can update their own details."""
        self._authenticate_user(self.login1_credentials)
        update_data = {"first_name": "UpdatedFirstName"}
        response = self.client.patch(f'/api/users/{self.user1.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        #print(response.data)
        self.assertEqual(response.data['first_name'], "UpdatedFirstName")
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.first_name, "UpdatedFirstName")

    def test_update_other_user_authenticated(self):
        """Test if authenticated user can update ANOTHER user's details (depends on permissions)."""
        self._authenticate_user(self.login1_credentials)
        update_data = {"first_name": "CannotUpdate"}
        response = self.client.patch(f'/api/users/{self.user2.id}/', update_data, format='json')
        # Default ModelViewSet allows any authenticated user to update any object.
        # You might want to add IsOwnerOrAdmin permission later.
        # For now, assuming default behavior:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # If you add stricter permissions, change this to HTTP_403_FORBIDDEN

    def test_delete_own_user_authenticated(self):
        """Test authenticated user can delete their own account."""
        self._authenticate_user(self.login1_credentials)
        response = self.client.delete(f'/api/users/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user1.id).exists())

    def test_delete_other_user_authenticated(self):
        """Test if authenticated user can delete ANOTHER user's account (depends on permissions)."""
        self._authenticate_user(self.login1_credentials)
        response = self.client.delete(f'/api/users/{self.user2.id}/')
        # Default ModelViewSet allows any authenticated user to delete any object.
        # You might want to add IsOwnerOrAdmin permission later.
        # For now, assuming default behavior:
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # If you add stricter permissions, change this to HTTP_403_FORBIDDEN
        self.assertFalse(User.objects.filter(id=self.user2.id).exists())

    def test_update_user_unauthenticated(self):
        """Test updating user requires authentication."""
        update_data = {"first_name": "ShouldFail"}
        response = self.client.patch(f'/api/users/{self.user1.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_user_unauthenticated(self):
        """Test deleting user requires authentication."""
        response = self.client.delete(f'/api/users/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Add tests for custom actions like 'communities' and 'matches' if needed
    def test_get_my_communities_authenticated(self):
        """Test getting communities for the authenticated user."""
        # Setup: Add user1 to a community (assuming Community model exists)
        # from community.models import Community, CommunityUsers
        # community = Community.objects.create(name="Test Comm")
        # CommunityUsers.objects.create(user=self.profile1, community=community, role="member")

        self._authenticate_user(self.login1_credentials)
        response = self.client.get('/api/users/communities/') # Assuming this is the correct URL from users/urls.py
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Add assertions based on expected community data

    def test_get_my_communities_unauthenticated(self):
        """Test getting communities requires authentication."""
        response = self.client.get('/api/users/communities/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)