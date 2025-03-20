from rest_framework import serializers
from .models import Match, MatchMoment, MatchSet
from users.models import UserProfile
from users.serializers import SimpleUserProfileSerializer
from django.db.models import Max

class MatchSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchSet
        fields = '__all__'

class MatchMomentSerializer(serializers.ModelSerializer):
    sets = MatchSetSerializer(many=True, read_only=True)
    class Meta:
        model = MatchMoment
        fields = '__all__'

class MatchSerializer(serializers.ModelSerializer):
    # Player details
    home1_details = SimpleUserProfileSerializer(source='home1', read_only=True)
    home2_details = SimpleUserProfileSerializer(source='home2', read_only=True)
    away1_details = SimpleUserProfileSerializer(source='away1', read_only=True)
    away2_details = SimpleUserProfileSerializer(source='away2', read_only=True)
    winner1_details = SimpleUserProfileSerializer(source='winner1', read_only=True)
    winner2_details = SimpleUserProfileSerializer(source='winner2', read_only=True)
    
    # Community name
    community_name = serializers.CharField(source='community_id.name', read_only=True)
    
    # Latest score information (formatted nicely)
    current_score = serializers.SerializerMethodField()
    match_status = serializers.SerializerMethodField()
    
    # For tournament matches
    tournament = serializers.SerializerMethodField()
    
    class Meta:
        model = Match
        fields = '__all__'
    
    def get_current_score(self, obj):
        """Return formatted current score"""
        latest_moment = obj.moments.order_by('-timestamp').first()
        if not latest_moment:
            return {"game": {"home": "0", "away": "0"}, 
                    "set": {"home": 0, "away": 0},
                    "match": {"home": 0, "away": 0}}
        
        # Return nicely formatted score
        return {
            "game": {
                "home": latest_moment.current_game_home,
                "away": latest_moment.current_game_away
            },
            "set": {
                "home": latest_moment.current_set_home,
                "away": latest_moment.current_set_away
            },
            "match": {
                "home": latest_moment.match_score_home,
                "away": latest_moment.match_score_away
            }
        }
    
    def get_match_status(self, obj):
        """Return match status (not started, in progress, completed)"""
        if not obj.moments.exists():
            return "not_started"
        if obj.winner1 or obj.winner2:
            return "completed"
        return "in_progress"
    
    def get_tournament(self, obj):
        """Return tournament information if match is part of a tournament"""
        from tournament.models import TournamentMatch
        try:
            t_match = TournamentMatch.objects.get(match=obj)
            return {
                "tournament_id": t_match.tournament.tournament_id,
                "tournament_name": t_match.tournament.name,
                "round": t_match.round,
                "match_number": t_match.match_number
            }
        except TournamentMatch.DoesNotExist:
            return None