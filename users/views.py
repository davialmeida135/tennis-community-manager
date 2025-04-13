from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from .models import UserProfile
from community.models import Community, CommunityUsers
from community.serializers import CommunitySerializer
from matches.models import Match
from matches.serializers import MatchSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication # If needed explicitly

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # Default auth/permissions are now handled by settings.py
    # authentication_classes = [JWTAuthentication] # Usually not needed here
    # permission_classes = [IsAuthenticated] # Usually not needed here

    def get_permissions(self):
        """Allow unauthenticated users to create a new account (register)."""
        # Allow anyone to create a user
        if self.action == 'create':
            return [] # Use AllowAny permission
        # For all other actions, use the default (IsAuthenticated)
        return super().get_permissions()

    
    @action(detail=False, methods=["get"])
    def communities(self, request):
        """Retorna as comunidades que o usuário pertence."""

        try:
            # Verifica se o usuário existe
            user = request.user
            user_profile = UserProfile.objects.get(user=user)
            
            # Get CommunityUsers entries
            community_users = CommunityUsers.objects.filter(user=user_profile)
            
            # Extract just the communities
            communities = [cu.community for cu in community_users]
            
            serializer = CommunitySerializer(communities, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
           return Response({"error": f"User {user} not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
           return Response({"error": str(e)+ str(user)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"])
    def matches(self, request):
        """Retorna as partidas que o usuário faz parte"""

        try:
            user = request.user
            user_profile = UserProfile.objects.get(user=user)
            user_matches = Match.objects.filter(home1=user_profile) | Match.objects.filter(home2=user_profile) | Match.objects.filter(away1=user_profile) | Match.objects.filter(away2=user_profile)
            serializer = MatchSerializer(user_matches, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({"error": f"User {user} not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)