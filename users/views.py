from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # Add authentication and permission classes
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # If you want to allow unauthenticated users to register
    def get_permissions(self):
        """Allow unauthenticated users to create a new account"""
        if self.action in ['create', 'login']:
            return []
        return super().get_permissions()

    @action(detail=False, methods=["post"])
    def login(self, request):
        """Autentica um usuário e retorna um token."""
        email = request.data.get("email")
        password = request.data.get("password")
        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password):
                token, created = Token.objects.get_or_create(user=user)
                return Response({"token": token.key, "user_id": user.id, "username": user.username}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """Realiza logout removendo o token do usuário."""
        if request.user.is_authenticated:
            request.user.auth_token.delete()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        return Response({"error": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)