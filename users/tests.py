from rest_framework.test import APITestCase
from rest_framework import status
from users.models import UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()

class UserTests(APITestCase):
    
    def setUp(self):
        self.user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "securepassword123",
            "profile": {
                "forehand": "Right",
                "backhand": "Left",
                "description": "Default profile description"
            }
        }
        self.user = User.objects.create_user(
            username=self.user_data["username"],
            email=self.user_data["email"],
            password=self.user_data["password"]
        )
        # Create the profile manually for setup
        # (If you're not using signals to auto-create profiles)
        self.profile = UserProfile.objects.create(
            user=self.user,
            forehand="Right",
            backhand="One Handed",
            description="Default profile description"
        )
    
    def test_create_user(self):
        """Testa a criação de um novo usuário."""
        new_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
        response = self.client.post('/api/users/', new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_login(self):
        """Testa o login do usuário com email e senha válidos."""
        response = self.client.post('/api/users/login/', {
            "email": self.user_data['email'],
            "password": self.user_data['password']
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
    
    def test_login_fail_invalid_email(self):
        """Testa login com e-mail inexistente."""
        response = self.client.post('/api/users/login/', {
            "email": "nonexistent@example.com",
            "password": self.user_data['password']
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_login_fail_invalid_password(self):
        """Testa login com senha incorreta."""
        response = self.client.post('/api/users/login/', {
            "email": self.user_data['email'],
            "password": "wrongpassword"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout(self):
        """Testa o logout removendo o token do usuário."""
        login_response = self.client.post('/api/users/login/', {
            "email": self.user_data['email'],
            "password": self.user_data['password']
        }, format='json')
        token = login_response.data['token']
        # Use the "Token" prefix as expected by DRF TokenAuthentication.
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.post('/api/users/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)