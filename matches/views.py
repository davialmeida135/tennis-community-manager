from django.shortcuts import render
from rest_framework import viewsets, status
import json
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from matches.models import Match, MatchMoment, MatchSet
from matches.serializers import MatchSerializer
from matches.match import TennisMatch, Game, Set, Tiebreak
from tournament.models import TournamentMatch
from users.models import UserProfile
import datetime
from rest_framework.permissions import IsAuthenticated
from .permissions import IsPlayerInMatchOrCommunityAdmin


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated]

    def _get_latest_moment(self, match):
        """Helper to get the most recent match moment"""
        return MatchMoment.objects.filter(match=match).order_by('-timestamp').first()

    def _create_tennis_match(self, match:Match, latest_moment=None):
        """Create a TennisMatch object from database state"""
        # Get player names from user profiles
        player1 = str(match.home1) if match.home1 else "Player 1"
        player2 = str(match.away1) if match.away1 else "Player 2" 
        
        # Create TennisMatch with proper configuration
        tennis_match = TennisMatch(
            player1, 
            player2, 
            match_id=match.match_id,
            best_of=match.max_sets,
            ad=match.ad
        )
        
        # Initialize the match
        tennis_match.start_match()
        
        if latest_moment:
            # Initialize the TennisMatch with data from the latest moment
            tennis_match.match_moment.match_score_h1 = latest_moment.match_score_home
            tennis_match.match_moment.match_score_a1 = latest_moment.match_score_away
            
            # Set current set scores
            tennis_match.match_moment.current_set.home1_score = latest_moment.current_set_home
            tennis_match.match_moment.current_set.away1_score = latest_moment.current_set_away
            
            # Get previous sets
            previous_sets = []
            for match_set in MatchSet.objects.filter(match_moment=latest_moment):
                previous_set = Set()
                previous_set.home1_score = match_set.home_games
                previous_set.away1_score = match_set.away_games
                previous_sets.append(previous_set)
            
            tennis_match.match_moment.sets = previous_sets
            
            # Set current game state
            if latest_moment.current_set_home == 6 and latest_moment.current_set_away == 6:
                # It's a tiebreak
                tiebreak = Tiebreak()
                tiebreak.home1_score = int(latest_moment.current_game_home) if latest_moment.current_game_home.isdigit() else 0
                tiebreak.away1_score = int(latest_moment.current_game_away) if latest_moment.current_game_away.isdigit() else 0
                tennis_match.match_moment.current_game = tiebreak
            else:
                # Regular game
                game = Game()
                game.home1_score = str(latest_moment.current_game_home)
                game.away1_score = str(latest_moment.current_game_away)
                tennis_match.match_moment.current_game = game
            
        return tennis_match

    def _save_tennis_match_state(self, match, tennis_match):
        """Save the state of a TennisMatch back to the database"""
        with transaction.atomic():
            # Create a new match moment
            match_moment = MatchMoment.objects.create(
                match=match,
                timestamp=datetime.datetime.now(),
                current_game_home=str(tennis_match.match_moment.current_game.home1_score),
                current_game_away=str(tennis_match.match_moment.current_game.away1_score),
                current_set_home=tennis_match.match_moment.current_set.home1_score,
                current_set_away=tennis_match.match_moment.current_set.away1_score,
                match_score_home=tennis_match.match_moment.match_score_h1,
                match_score_away=tennis_match.match_moment.match_score_a1,
            )
            
            # Create records for completed sets
            for i, set_data in enumerate(tennis_match.match_moment.sets):
                MatchSet.objects.create(
                    match_moment=match_moment,
                    set_number=i+1,
                    home_games=set_data.home1_score,
                    away_games=set_data.away1_score,
                )
                
            return match_moment

    @action(detail=True, methods=["post"], permission_classes=[IsPlayerInMatchOrCommunityAdmin])
    def start_match(self, request, pk=None):
        """Initialize a new match with proper tennis scoring"""
        match = self.get_object()
        
        # Create a TennisMatch object
        tennis_match = self._create_tennis_match(match)
        
        # Save initial state to database
        self._save_tennis_match_state(match, tennis_match)
        
        return Response({"message": "Match started successfully"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsPlayerInMatchOrCommunityAdmin])
    def point_home(self, request, pk=None):
        """Add point for home player using proper tennis logic"""
        match = self.get_object()
        latest_moment = self._get_latest_moment(match)
        
        if not latest_moment:
            return Response({"error": "Match must be started first"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a TennisMatch object with current state
        tennis_match = self._create_tennis_match(match, latest_moment)
        
        # Apply the point logic from match.py
        tennis_match.point(tennis_match.home1)
        
        # Save the updated state back to database
        new_moment = self._save_tennis_match_state(match, tennis_match)
        
        # Update match winner if match is complete
        if tennis_match.match_moment.match_score_h1 > match.max_sets / 2:
            match.winner1 = match.home1
            self.set_winner(request = json.dumps({"winner_id": match.home1.user.id}), pk=pk)
            match.save()
            
        return Response({
            "message": "Point for home player recorded successfully",
            "current_score": {
                "game": {
                    "home": str(tennis_match.match_moment.current_game.home1_score),
                    "away": str(tennis_match.match_moment.current_game.away1_score)
                },
                "set": {
                    "home": tennis_match.match_moment.current_set.home1_score,
                    "away": tennis_match.match_moment.current_set.away1_score
                },
                "match": {
                    "home": tennis_match.match_moment.match_score_h1,
                    "away": tennis_match.match_moment.match_score_a1
                }
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsPlayerInMatchOrCommunityAdmin])
    def point_away(self, request, pk=None):
        """Add point for away player using proper tennis logic"""
        match = self.get_object()
        latest_moment = self._get_latest_moment(match)
        
        if not latest_moment:
            return Response({"error": "Match must be started first"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a TennisMatch object with current state
        tennis_match = self._create_tennis_match(match, latest_moment)
        
        # Apply the point logic from match.py
        tennis_match.point(tennis_match.away1)
        
        # Save the updated state back to database
        new_moment = self._save_tennis_match_state(match, tennis_match)
        
        # Update match winner if match is complete
        if tennis_match.match_moment.match_score_a1 > match.max_sets / 2:
            match.winner1 = match.away1
            self.set_winner(request = json.dumps({"winner_id": match.away1.user.id}), pk=pk)
            match.save()
            
        return Response({
            "message": "Point for away player recorded successfully",
            "current_score": {
                "game": {
                    "home": str(tennis_match.match_moment.current_game.home1_score),
                    "away": str(tennis_match.match_moment.current_game.away1_score)
                },
                "set": {
                    "home": tennis_match.match_moment.current_set.home1_score,
                    "away": tennis_match.match_moment.current_set.away1_score
                },
                "match": {
                    "home": tennis_match.match_moment.match_score_h1,
                    "away": tennis_match.match_moment.match_score_a1
                }
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["post"], permission_classes=[IsPlayerInMatchOrCommunityAdmin])
    def set_winner(self, request, pk=None, ):
        """Set the winner of the match"""
        try:
            match = self.get_object()
            winner_id = request.data.get("winner_id")

            if not match:
                return Response({"error": "Match not found"}, status=status.HTTP_404_NOT_FOUND)
            
            if not winner_id:
                return Response({"error": "Winner ID must be provided"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                home1_id = match.home1.user.id
            except Exception as e:
                home1_id = None
            
            try:
                away1_id = match.away1.user.id
            except Exception as e:
                away1_id = None

            if home1_id != winner_id and away1_id != winner_id:
                return Response({"error": "Winner must be one of the players"}, status=status.HTTP_400_BAD_REQUEST)
            
            winner_profile = UserProfile.objects.get(pk=winner_id)
            # Set the winner of the match
            match.winner1 = winner_profile
            match.save()

            # Checar se a partida é de torneio e passar jogador para a próxima rodada
            tournament_match = TournamentMatch.objects.get(match=match)
            if tournament_match:
                next_match = tournament_match.next_match
                if next_match:
                    if next_match.home1 is None:
                        next_match.home1 = winner_profile
                    elif next_match.away1 is None:
                        next_match.away1 = winner_profile
                    next_match.save()
                else:
                    # TODO Campeão
                    print("Parabens ganhou o torneio")
            
            return Response({"message": "Match winner set successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)