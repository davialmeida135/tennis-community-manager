from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

# Simplified User serializer for nested use
class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

# Simplified UserProfile serializer for nested use
class SimpleUserProfileSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'forehand', 'backhand', 'picture']

class UserSerializer(serializers.ModelSerializer):
    # Allow passing extra profile data in the "profile" field
    profile = serializers.DictField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "profile"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        profile_data = validated_data.pop("profile", {})
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if "password" in validated_data:
            instance.set_password(validated_data["password"])
            
        instance.save()
        # update profile if provided
        profile = instance.profile
        for key, value in profile_data.items():
            setattr(profile, key, value)
        profile.save()
        return instance