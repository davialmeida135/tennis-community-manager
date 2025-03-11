from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import Community, CommunityUsers
from users.models import UserProfile
from .serializers import CommunitySerializer, CommunityUsersSerializer
from django.contrib.auth import get_user_model
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

User = get_user_model()


class CommunityViewSet(viewsets.ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
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
        CommunityUsers.objects.create(
            community=community,
            user=user_profile,  # associa o usuário existente
        )

        return Response(
            {"message": "Usuário adicionado com sucesso"},
            status=status.HTTP_201_CREATED
        )
