from django.test import TestCase
from .utils import seeding_order, fill_null_seeds, fit_players_in_bracket
# Create your tests here.

def test_brackets():
    class Player():
        def __init__(self, name,seed = None):
            self.name = name
            self.seed = seed
        def __str__(self):
            return f"{self.name} seeded {self.seed}"
        
        def save(self):
            return
    
    class Match():
        def __init__(self, round= None, number= None, home = None, away = None, next_match = None):
            self.round = round
            self.number = number
            self.home = home
            self.away = away
            self.next_match = next_match

        def __str__(self):
            return f"{self.home} vs {self.away}, Round {self.round}, Match {self.number}"
        
        def save(self):
            return
        
    players = [Player(f"Player {i}") for i in range(1, 10)]
    for i in range(0,6):
        players[i].seed = i+1

    for player in players:
        print(player)

    print("Removing null seeds")

    # Garantir que o número de jogadores seja uma potência de 2
    bracket_size = 2
    while len(players) > bracket_size:
        bracket_size *= 2

    seeded = fill_null_seeds(players, bracket_size)
    for player in seeded:
        print(player)

    match_order = seeding_order(bracket_size)
    print("Match order: ",match_order)

    sorted_players = fit_players_in_bracket(seeded, match_order)
    sorted_players = sorted_players[::-1]

    for player in sorted_players:
        print(player)

    matches = []
    next_round_matches = [] 

    round_number = 1
    match_number = 1
    while len(sorted_players) >= 2:
        p1, p2 = sorted_players.pop(), sorted_players.pop()
        match = Match(round_number, match_number, p1, p2)
        
        matches.append(match)
        next_round_matches.append(match)
        print(match)
        match_number += 1

    # Criando rodadas subsequentes
    while len(next_round_matches) > 1:
        current_round_matches = next_round_matches
        next_round_matches = []
        round_number += 1
        match_number = 1

        while len(current_round_matches) >= 2:
            current_round_matches = current_round_matches[::-1]
            m1, m2 = current_round_matches.pop(), current_round_matches.pop()
            match = Match(round_number, match_number, None, None)

            if round_number == 2:
                m1_bye = None
                m2_bye = None
                if not m1.home:
                    m1_bye = m1.away
                elif not m1.away:
                    m1_bye = m1.home
                if not m2.home:
                    m2_bye = m2.away
                elif not m2.away:
                    m2_bye = m2.home
                
                match = Match(round_number, match_number, m1_bye, m2_bye)

            print(match)

            # Conectar partidas anteriores com a próxima
            m1.next_match = match
            m1.save()
            m2.next_match = match
            m2.save()

            next_round_matches.append(match)
            match_number += 1

    return "Success"



from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from tournament.models import Tournament, TournamentPlayer, TournamentMatch
from community.models import Community
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()

class TournamentViewSetTests(APITestCase):
    def setUp(self):
        # Create a community
        self.community = Community.objects.create(
            name="Test Community", 
            description="A test community"
        )
        # Create a tournament
        self.tournament = Tournament.objects.create(
            community_id=self.community,
            name="Test Tournament",
            type="single_elimination"
        )
        # Create two players (users and their profiles)
        self.user1 = User.objects.create_user(
            username="player1",
            email="player1@test.com",
            password="pass"
        )
        self.user2 = User.objects.create_user(
            username="player2",
            email="player2@test.com",
            password="pass"
        )
        self.user3 = User.objects.create_user(
            username="player3",
            email="player3@test.com",
            password="pass"
        )
        self.user4 = User.objects.create_user(
            username="player4",
            email="player4@test.com",
            password="pass"
        )
        self.user5 = User.objects.create_user(
            username="player5",
            email="player5@test.com",
            password="pass"
        )
        self.user6 = User.objects.create_user(
            username="player6",
            email="player6@test.com",
            password="pass"
        )
        self.user7 = User.objects.create_user(
            username="player7",
            email="player7@test.com",
            password="pass"
        )
        self.user8 = User.objects.create_user(
            username="player8",
            email="player8@test.com",
            password="pass"
        )
        self.user9 = User.objects.create_user(
            username="player9",
            email="player9@test.com",
            password="pass"
        )
    
        self.profile1 = UserProfile.objects.create(user=self.user1)
        self.profile2 = UserProfile.objects.create(user=self.user2)
        self.profile3 = UserProfile.objects.create(user=self.user3)
        self.profile4 = UserProfile.objects.create(user=self.user4)
        self.profile5 = UserProfile.objects.create(user=self.user5)
        self.profile6 = UserProfile.objects.create(user=self.user6)
        self.profile7 = UserProfile.objects.create(user=self.user7)
        self.profile8 = UserProfile.objects.create(user=self.user8)
        self.profile9 = UserProfile.objects.create(user=self.user9)
        # Create TournamentPlayer entries with seeds
        TournamentPlayer.objects.create(
            tournament=self.tournament,
            user=self.profile1,
            seed=1
        )
        TournamentPlayer.objects.create(
            tournament=self.tournament,
            user=self.profile2,
            seed=2
        )
        TournamentPlayer.objects.create(
            tournament=self.tournament,
            user=self.profile3,
            seed=3
        )
        TournamentPlayer.objects.create(
            tournament=self.tournament,
            user=self.profile4,
            seed=None
        )
        TournamentPlayer.objects.create(
            tournament=self.tournament,
            user=self.profile5,
            seed=None
        )
        TournamentPlayer.objects.create(
            tournament=self.tournament,
            user=self.profile6,
            seed=None
        )
        TournamentPlayer.objects.create(
            tournament=self.tournament,
            user=self.profile7,
            seed=None
        )
        TournamentPlayer.objects.create(
            tournament=self.tournament,
            user=self.profile8,
            seed=None
        )
        TournamentPlayer.objects.create(
            tournament=self.tournament,
            user=self.profile9,
            seed=None
        )

    def test_generate_bracket_success(self):
        """
        Test that the generate_bracket endpoint creates tournament matches.
        """
        # Assuming the tournament viewset is registered at /api/tournament/<id>/...
        url = f"/api/tournament/{self.tournament.pk}/generate_bracket/"
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        matches = TournamentMatch.objects.filter(tournament=self.tournament)
        self.assertTrue(matches.exists())

    def test_print_tournament_matches(self):
        """
        Test a helper way to print out tournament matches along with player seeds.
        """
        # First, generate the bracket.
        url = f"/api/tournament/{self.tournament.pk}/generate_bracket/"
        self.client.post(url, {}, format="json")
        matches = TournamentMatch.objects.filter(tournament=self.tournament).order_by("round", "match_number")
        output_lines = []
        for match in matches:
            home_user = match.match.home1
            away_user = match.match.away1

            # Look up the seed from TournamentPlayer for this tournament and player (if exists)
            home_seed = None
            away_seed = None
            if home_user:
                tp = TournamentPlayer.objects.filter(tournament=self.tournament, user=home_user).first()
                if tp:
                    home_seed = tp.seed
            if away_user:
                tp = TournamentPlayer.objects.filter(tournament=self.tournament, user=away_user).first()
                if tp:
                    away_seed = tp.seed

            output_lines.append(
                f"{str(match)} - Home: {home_user} (Seed: {home_seed}) vs Away: {away_user} (Seed: {away_seed})"
            )
        printed_output = "\n".join(output_lines)
        self.assertTrue(len(printed_output) > 0)
        print("Tournament Matches:\n", printed_output)