from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from users.models import UserProfile
from rest_framework.authtoken.models import Token
from matches.models import Match, MatchMoment, MatchSet
from matches.match import TennisMatch, Game, Set, Tiebreak

User = get_user_model()

class MatchLogicTests(TestCase):
    """Tests for the tennis match scoring logic in match.py"""
    
    def setUp(self):
        self.tennis_match = TennisMatch('Player 1', 'Player 2', match_id=1)
        self.tennis_match.start_match()
    
    def test_game_scoring(self):
        """Test scoring within a game follows tennis rules"""
        # Initial score
        self.assertEqual(self.tennis_match.match_moment.current_game.home1_score, '0')
        self.assertEqual(self.tennis_match.match_moment.current_game.away1_score, '0')
        
        # Score progression: 0 -> 15 -> 30 -> 40
        self.tennis_match.point('Player 1')
        self.assertEqual(self.tennis_match.match_moment.current_game.home1_score, '15')
        
        self.tennis_match.point('Player 1')
        self.assertEqual(self.tennis_match.match_moment.current_game.home1_score, '30')
        
        self.tennis_match.point('Player 1')
        self.assertEqual(self.tennis_match.match_moment.current_game.home1_score, '40')
    
    def test_advantage_scoring(self):
        """Test advantage scoring when deuce"""
        # Get to deuce
        for _ in range(3):
            self.tennis_match.point('Player 1')
            self.tennis_match.point('Player 2')
        
        self.assertEqual(self.tennis_match.match_moment.current_game.home1_score, '40')
        self.assertEqual(self.tennis_match.match_moment.current_game.away1_score, '40')
        
        # Player 1 gets advantage
        self.tennis_match.point('Player 1')
        self.assertEqual(self.tennis_match.match_moment.current_game.home1_score, 'AD')
        self.assertEqual(self.tennis_match.match_moment.current_game.away1_score, '40')
        
        # Back to deuce
        self.tennis_match.point('Player 2')
        self.assertEqual(self.tennis_match.match_moment.current_game.home1_score, '40')
        self.assertEqual(self.tennis_match.match_moment.current_game.away1_score, '40')
    
    def test_game_win(self):
        """Test winning a game increases set score"""
        # Win a game with player 1
        for _ in range(4):
            self.tennis_match.point('Player 1')
        
        self.assertEqual(self.tennis_match.match_moment.current_set.home1_score, 1)
        self.assertEqual(self.tennis_match.match_moment.current_set.away1_score, 0)
        
        # Verify game score reset
        self.assertEqual(self.tennis_match.match_moment.current_game.home1_score, '0')
        self.assertEqual(self.tennis_match.match_moment.current_game.away1_score, '0')
    
    def test_set_win(self):
        """Test winning a set increases match score"""
        # Win 6 games with player 1
        for _ in range(24):  # 4 points per game * 6 games
            self.tennis_match.point('Player 1')
        
        self.assertEqual(self.tennis_match.match_moment.match_score_h1, 1)
        self.assertEqual(self.tennis_match.match_moment.match_score_a1, 0)
        
        # Verify set score reset and moved to sets list
        self.assertEqual(len(self.tennis_match.match_moment.sets), 1)
        self.assertEqual(self.tennis_match.match_moment.current_set.home1_score, 0)
        self.assertEqual(self.tennis_match.match_moment.current_set.away1_score, 0)
    
    def test_tiebreak(self):
        """Test that a tiebreak is triggered at 6-6"""
        # Get to 6-6
        for i in range(12):
            for _ in range(4):  # 4 points in a game
                if i % 2 == 0:
                    self.tennis_match.point('Player 1')
                else:
                    self.tennis_match.point('Player 2')
        
        # Verify tiebreak mode
        self.assertIsInstance(self.tennis_match.match_moment.current_game, Tiebreak)
        
        # Score some tiebreak points
        self.tennis_match.point('Player 1')
        self.assertEqual(self.tennis_match.match_moment.current_game.home1_score, 1)
        
        # Win tiebreak
        for _ in range(7):
            self.tennis_match.point('Player 1')
        
        # Set should be won
        self.assertEqual(self.tennis_match.match_moment.match_score_h1, 1)


class MatchAPITests(APITestCase):
    """Tests for the matches API endpoints"""
    
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            forehand='Right',
            backhand='One-handed'
        )
        
        # Create token for authentication
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create a match
        self.match = Match.objects.create(
            home1=self.profile,
            max_sets=3,
            ad=True
        )
    
    def test_start_match(self):
        """Test starting a match initializes the scoring state"""
        url = f'/api/matches/{self.match.match_id}/start_match/'
        print("Starting match at URL:", url)
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify initial state was created
        moments = MatchMoment.objects.filter(match=self.match)
        self.assertEqual(moments.count(), 1)
        
        # Check initial scores
        moment = moments.first()
        self.assertEqual(moment.current_game_home, '0')
        self.assertEqual(moment.current_game_away, '0')
        self.assertEqual(moment.current_set_home, 0)
        self.assertEqual(moment.current_set_away, 0)
        self.assertEqual(moment.match_score_home, 0)
        self.assertEqual(moment.match_score_away, 0)
    
    def test_point_home(self):
        """Test adding a point for the home player"""
        # Start match first
        start_url = f'/api/matches/{self.match.match_id}/start_match/'
        self.client.post(start_url)
        
        # Add a point for home
        url = f'/api/matches/{self.match.match_id}/point_home/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify score updated
        self.assertEqual(response.data['current_score']['game']['home'], "15")
        self.assertEqual(response.data['current_score']['game']['away'], "0")
        
        # Check database state
        moment = MatchMoment.objects.filter(match=self.match).order_by('-timestamp').first()
        self.assertEqual(moment.current_game_home, '15')
    
    def test_point_away(self):
        """Test adding a point for the away player"""
        # Start match first
        start_url = f'/api/matches/{self.match.match_id}/start_match/'
        self.client.post(start_url)
        
        # Add a point for away
        url = f'/api/matches/{self.match.match_id}/point_away/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify score updated
        self.assertEqual(response.data['current_score']['game']['home'], '0')
        self.assertEqual(response.data['current_score']['game']['away'], '15')
        
        # Check database state
        moment = MatchMoment.objects.filter(match=self.match).order_by('-timestamp').first()
        self.assertEqual(moment.current_game_away, '15')
    
    def test_game_progression(self):
        """Test a complete game sequence through the API"""
        # Start match first
        start_url = f'/api/matches/{self.match.match_id}/start_match/'
        self.client.post(start_url)
        
        # Win a game for home player
        point_url = f'/api/matches/{self.match.match_id}/point_home/'
        
        for _ in range(4):  # 4 points to win a game
            response = self.client.post(point_url)
        
        # Verify game was won and set score updated
        self.assertEqual(response.data['current_score']['set']['home'], 1)
        self.assertEqual(response.data['current_score']['set']['away'], 0)
        
        # Game score should reset
        self.assertEqual(response.data['current_score']['game']['home'], '0')
        self.assertEqual(response.data['current_score']['game']['away'], '0')
    
    def test_game_to_deuce(self):
        """Test a game that goes to deuce through the API"""
        # Start match first
        start_url = f'/api/matches/{self.match.match_id}/start_match/'
        self.client.post(start_url)
        
        # Get to deuce (both 40-40)
        point_home_url = f'/api/matches/{self.match.match_id}/point_home/'
        point_away_url = f'/api/matches/{self.match.match_id}/point_away/'
        
        for _ in range(3):
            self.client.post(point_home_url)
            self.client.post(point_away_url)
        
        # Verify deuce
        moment = MatchMoment.objects.filter(match=self.match).order_by('-timestamp').first()
        self.assertEqual(moment.current_game_home, '40')
        self.assertEqual(moment.current_game_away, '40')

    def test_ad(self):
        """Test a match that goes to a tiebreak through the API"""
        # Start match first
        start_url = f'/api/matches/{self.match.match_id}/start_match/'
        self.client.post(start_url)
        
        
        point_home_url = f'/api/matches/{self.match.match_id}/point_home/'
        point_away_url = f'/api/matches/{self.match.match_id}/point_away/'
        
        for _ in range(6):
            self.client.post(point_home_url)
            self.client.post(point_away_url)

        moment = MatchMoment.objects.filter(match=self.match).order_by('-timestamp').first()
        self.assertEqual(moment.current_game_home, '40')
        self.assertEqual(moment.current_game_away, '40')
    
    def test_tiebreak(self):
        start_url = f'/api/matches/{self.match.match_id}/start_match/'
        self.client.post(start_url)
        point_home_url = f'/api/matches/{self.match.match_id}/point_home/'
        point_away_url = f'/api/matches/{self.match.match_id}/point_away/'
  
        for _ in range(20):
            self.client.post(point_home_url)
        for i in range(24):
            self.client.post(point_away_url)
        for i in range(6):
            self.client.post(point_home_url)
        self.client.post(point_away_url)

        moment = MatchMoment.objects.filter(match=self.match).order_by('-timestamp').first()
        self.assertEqual(moment.current_game_home, '2')
        self.assertEqual(moment.current_game_away, '1')
        self.assertEqual(moment.current_set_home, 6)
        self.assertEqual(moment.current_set_away, 6)
        

    def test_unauthorized_access(self):
        """Test that unauthenticated requests are rejected"""
        # Remove authentication credentials
        self.client.credentials()
        
        url = f'/api/matches/{self.match.match_id}/start_match/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)