from rest_framework import serializers
from .models import CommunityUsers, Community
from users.models import UserProfile
from users.serializers import SimpleUserProfileSerializer
from django.db import transaction

class CommunityUsersSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    user = SimpleUserProfileSerializer(read_only=True)
    class Meta:
        model = CommunityUsers
        fields = "__all__"

class CommunitySerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        with transaction.atomic():
            # Cria comunidade
            community = super().create(validated_data)
            
            # Pega usuário que fez o request
            user = self.context['request'].user
            user = UserProfile.objects.get(user=user)
            
            # Adiciona ele como dono da comunidade
            CommunityUsers.objects.create(
                user=user,
                community=community,
                role="owner"
            )
            
            return community
    
    class Meta:
        model = Community
        fields = "__all__"