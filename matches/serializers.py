from rest_framework import serializers
from .models import Match, MatchMoment, MatchSet

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'

class MatchSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchSet
        fields = '__all__'

class MatchMomentSerializer(serializers.ModelSerializer):
    sets = MatchSetSerializer(many=True, read_only=True)

    class Meta:
        model = MatchMoment
        fields = '__all__'