from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from community.models import Community, CommunityUsers
from users.models import UserProfile
from rest_framework.authtoken.models import Token

User = get_user_model()

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
            role='admin'
        )
        
        self.assertEqual(community_user.community, self.community)
        self.assertEqual(community_user.user, self.profile)
        self.assertEqual(community_user.role, 'admin')

class CommunityAPITests(APITestCase):
    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpass123'
        )
        
        # Create profiles
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            forehand='Right',
            backhand='Two-handed'
        )
        self.regular_profile = UserProfile.objects.create(
            user=self.regular_user,
            forehand='Left',
            backhand='One-handed'
        )
        
        # Create tokens for authentication
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.regular_token = Token.objects.create(user=self.regular_user)
        
    def test_create_community_authenticated(self):
        """Test that an authenticated user can create a community"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        data = {
            'name': 'New Tennis Club',
            'description': 'A brand new tennis community'
        }
        
        response = self.client.post('/api/communities/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if community was created
        community = Community.objects.get(name='New Tennis Club')
        self.assertEqual(community.description, 'A brand new tennis community')
        
        # Check if user was added as admin
        community_user = CommunityUsers.objects.get(community=community)
        self.assertEqual(community_user.user, self.admin_profile)
        self.assertEqual(community_user.role, 'ADMIN')
        
    def test_create_community_unauthenticated(self):
        """Test that unauthenticated users can't create communities"""
        data = {
            'name': 'Unauthenticated Club',
            'description': 'This should fail'
        }
        
        response = self.client.post('/api/communities/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_add_user_to_community(self):
        """Test adding a user to an existing community"""
        # First create a community as admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        community_data = {
            'name': 'Members Club',
            'description': 'A club to test adding members'
        }
        
        self.client.post('/api/communities/', community_data, format='json')
        community = Community.objects.get(name='Members Club')
        
        # Now add the regular user to this community
        add_user_data = {
            'id': self.regular_profile.id
        }
        
        response = self.client.post(f'/api/communities/{community.community_id}/add_user/', add_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if user was added
        community_user = CommunityUsers.objects.get(community=community, user=self.regular_profile)
        self.assertIsNotNone(community_user)
        
    def test_list_communities(self):
        """Test listing all communities"""
        # Create some communities first
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        self.client.post('/api/communities/', {'name': 'Club 1', 'description': 'First club'}, format='json')
        self.client.post('/api/communities/', {'name': 'Club 2', 'description': 'Second club'}, format='json')
        
        # List communities
        response = self.client.get('/api/communities/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)