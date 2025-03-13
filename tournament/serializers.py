from rest_framework import serializers
from .models import Tournament, TournamentPlayer, TournamentMatch
from matches.models import Match
from django.contrib.auth import get_user_model
User = get_user_model()

class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = '__all__'

class TournamentPlayerSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(source="user", queryset=User.objects.all())

    class Meta:
        model = TournamentPlayer
        fields = ['id', 'tournament', 'user_id', 'seed', 'status']

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'

class TournamentMatchSerializer(serializers.ModelSerializer):
    match = MatchSerializer()  # Serializa os detalhes da partida
    next_match_id = serializers.PrimaryKeyRelatedField(source='next_match', queryset=TournamentMatch.objects.all(), allow_null=True, required=False)

    class Meta:
        model = TournamentMatch
        fields = ['match', 'tournament', 'match_number', 'round', 'next_match_id']