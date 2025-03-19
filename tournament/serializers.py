from rest_framework import serializers
from .models import Tournament, TournamentPlayer, TournamentMatch
from matches.serializers import MatchSerializer
from matches.models import Match
from users.serializers import SimpleUserProfileSerializer
from django.contrib.auth import get_user_model
User = get_user_model()

class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = '__all__'

class TournamentPlayerSerializer(serializers.ModelSerializer):
    #user_id = serializers.PrimaryKeyRelatedField(source="user", queryset=User.objects.all())
    user = SimpleUserProfileSerializer(read_only=True)
    class Meta:
        model = TournamentPlayer
        #fields = ['id', 'tournament', 'user_id', 'seed', 'status']
        fields = ['tournament', 'seed', 'user','status']

class TournamentMatchSerializer(serializers.ModelSerializer):
    match = MatchSerializer()  # Serializa os detalhes da partida
    next_match_id = serializers.PrimaryKeyRelatedField(source='next_match', queryset=Match.objects.all(), allow_null=True, required=False)

    class Meta:
        model = TournamentMatch
        fields = ['match', 'tournament', 'match_number', 'round', 'next_match_id']