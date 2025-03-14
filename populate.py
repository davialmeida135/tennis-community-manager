import os
import django
import random
import datetime
from django.utils import timezone
from django.db import transaction

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

# Import models after Django setup
from django.contrib.auth import get_user_model
from users.models import UserProfile
from community.models import Community, CommunityUsers
from matches.models import Match, MatchMoment, MatchSet
from tournament.models import Tournament, TournamentPlayer, TournamentMatch
from django.contrib.auth.hashers import make_password
from matches.match import TennisMatch

User = get_user_model()

# Configuration
NUM_USERS = 50
NUM_COMMUNITIES = 10
NUM_MATCHES = 100
NUM_TOURNAMENTS = 5
PASSWORD = "tennis123"  # Default password for all users

first_names = [
    "João", "Maria", "Pedro", "Ana", "Lucas", "Julia", "Carlos", "Mariana", 
    "Rafael", "Fernanda", "Diego", "Camila", "Gustavo", "Beatriz", "Ricardo", 
    "Amanda", "Daniel", "Leticia", "Fernando", "Patricia", "Rodrigo", "Natalia",
    "Leonardo", "Gabriela", "Eduardo", "Carolina", "Felipe", "Larissa", "Marcus",
    "Vanessa", "Bruno", "Bianca", "André", "Jéssica", "Alexandre", "Isabela",
    "Thiago", "Luana", "Roberto", "Renata", "Leandro", "Vitoria", "Marcelo",
    "Débora", "Raul", "Priscila", "Vitor", "Monica", "Sergio", "Juliana"
]

last_names = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Almeida",
    "Pereira", "Lima", "Gomes", "Ribeiro", "Martins", "Costa", "Carvalho", 
    "Teixeira", "Alves", "Barbosa", "Pinto", "Lopes", "Fernandes", "Monteiro",
    "Marques", "Gonçalves", "Cardoso", "Nunes", "Ramos", "Vieira", "Mendes",
    "Freitas", "Dias", "Correia", "Nascimento", "Araujo", "Moreira", "Moura",
    "Cavalcanti", "Rocha", "Machado", "Barros", "Melo", "Andrade", "Castro",
    "Campos", "Rezende", "Duarte", "Farias", "Miranda", "Guimarães", "Nogueira",
    "Schmitz", "Müller"
]

forehands = ["One handed", "Two handed", "Flat", "Heavy topspin", "Slice"]
backhands = ["One handed", "Two handed", "Flat", "Heavy topspin", "Slice"]

community_names = [
    "São Paulo Tennis Club", "Rio Tennis Association", "Brasília Tennis Center",
    "Curitiba Tennis Society", "Salvador Tennis Club", "Porto Alegre Tennis Group",
    "Belo Horizonte Tennis Community", "Florianópolis Beach Tennis",
    "Amazônia Tennis Club", "Recife Tennis Enthusiasts"
]

descriptions = [
    "A community for tennis lovers in the area",
    "Practice, compete, and enjoy tennis together",
    "For beginners to advanced players",
    "Competitive tennis and social events",
    "Play tennis and make friends"
]

# Helper function to create a simulated tennis match result
def simulate_tennis_match(match_obj, winner=None):
    """Simulates a tennis match and updates the database with the result"""
    home1_name = str(match_obj.home1) if match_obj.home1 else "Player 1"
    away1_name = str(match_obj.away1) if match_obj.away1 else "Player 2"
    
    tennis_match = TennisMatch(
        home1_name,
        away1_name,
        match_id=match_obj.match_id,
        best_of=match_obj.max_sets
    )
    
    tennis_match.start_match()
    
    # Decide winner if not specified
    if winner is None:
        winner = random.choice([home1_name, away1_name])
    
    # Simulate match play until someone wins
    while (tennis_match.match_moment.match_score_h1 < match_obj.max_sets / 2 and 
           tennis_match.match_moment.match_score_a1 < match_obj.max_sets / 2):
        
        # Weighted randomization for more realistic scores
        if winner == home1_name:
            player = random.choices(
                [home1_name, away1_name], 
                weights=[0.7, 0.3], 
                k=1
            )[0]
        else:
            player = random.choices(
                [home1_name, away1_name], 
                weights=[0.3, 0.7], 
                k=1
            )[0]
            
        tennis_match.point(player)
    
    # Save match result to database
    match_moment = MatchMoment.objects.create(
        match=match_obj,
        timestamp=timezone.now(),
        current_game_home=str(tennis_match.match_moment.current_game.home1_score),
        current_game_away=str(tennis_match.match_moment.current_game.away1_score),
        current_set_home=tennis_match.match_moment.current_set.home1_score,
        current_set_away=tennis_match.match_moment.current_set.away1_score,
        match_score_home=tennis_match.match_moment.match_score_h1,
        match_score_away=tennis_match.match_moment.match_score_a1,
    )
    
    # Save completed sets
    for i, set_data in enumerate(tennis_match.match_moment.sets):
        MatchSet.objects.create(
            match_moment=match_moment,
            set_number=i+1,
            home_games=set_data.home1_score,
            away_games=set_data.away1_score,
        )
    
    # Update match winner
    if tennis_match.match_moment.match_score_h1 > tennis_match.match_moment.match_score_a1:
        match_obj.winner1 = match_obj.home1
    else:
        match_obj.winner1 = match_obj.away1
    
    match_obj.save()
    return match_obj

def run():
    """Main function to populate the database"""
    with transaction.atomic():
        print("Creating users and profiles...")
        users = []
        profiles = []
        
        # Create users and profiles
        for i in range(NUM_USERS):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
            email = f"{username}@example.com"
            
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(PASSWORD),
                first_name=first_name,
                last_name=last_name
            )
            users.append(user)
            
            profile = UserProfile.objects.create(
                user=user,
                forehand=random.choice(forehands),
                backhand=random.choice(backhands),
                description=f"Tennis player with {random.randint(1, 20)} years of experience"
            )
            profiles.append(profile)
            
        print(f"Created {len(users)} users and profiles")
        
        print("Creating communities...")
        communities = []
        
        # Create communities
        for i in range(NUM_COMMUNITIES):
            community = Community.objects.create(
                name=community_names[i] if i < len(community_names) else f"Tennis Community {i+1}",
                description=random.choice(descriptions)
            )
            communities.append(community)
            
            # Add members to communities
            num_members = random.randint(5, 30)  # Random number of members per community
            selected_profiles = random.sample(profiles, num_members)
            
            # First user is admin
            CommunityUsers.objects.create(
                community=community,
                user=selected_profiles[0],
                role="admin"
            )
            
            # Some moderators
            for profile in selected_profiles[1:4]:
                CommunityUsers.objects.create(
                    community=community,
                    user=profile,
                    role="moderator"
                )
            
            # Rest are regular members
            for profile in selected_profiles[4:]:
                CommunityUsers.objects.create(
                    community=community,
                    user=profile,
                    role="member"
                )
                
        print(f"Created {len(communities)} communities with members")
        
        print("Creating matches...")
        matches = []
        
        # Create matches
        for i in range(NUM_MATCHES):
            # Select a random community
            community = random.choice(communities)
            
            # Get community members
            community_members = [cu.user for cu in CommunityUsers.objects.filter(community=community)]
            
            if len(community_members) >= 2:
                # Select two different players
                home_player, away_player = random.sample(community_members, 2)
                
                # Create match
                match_date = timezone.now() - datetime.timedelta(days=random.randint(0, 60))
                
                match = Match.objects.create(
                    community_id=community,
                    match_date=match_date,
                    home1=home_player,
                    away1=away_player,
                    max_sets=random.choice([3, 5]),
                    ad=True
                )
                
                # Simulate match result
                simulate_tennis_match(match)
                matches.append(match)
                
        print(f"Created {len(matches)} matches")
        
        print("Creating tournaments...")
        tournaments = []
        
        # Create tournaments
        for i in range(NUM_TOURNAMENTS):
            community = random.choice(communities)
            
            tournament = Tournament.objects.create(
                name=f"{community.name} Tournament {i+1}",
                community_id=community,
                type="single_elimination"
            )
            tournaments.append(tournament)
            
            # Get community members
            community_members = [cu.user for cu in CommunityUsers.objects.filter(community=community)]
            
            # Register players (8-16 players)
            num_players = random.randint(8, 16)
            if len(community_members) >= num_players:
                players = random.sample(community_members, num_players)
                
                # Create tournament players, some with seeds
                for j, player in enumerate(players):
                    seed = j+1 if j < 4 else None  # Only seed top 4 players
                    TournamentPlayer.objects.create(
                        tournament=tournament,
                        user=player,
                        seed=seed,
                        status="registered"
                    )
                
                # Generate tournament bracket
                from tournament.utils import seeding_order, fill_null_seeds, fit_players_in_bracket
                
                # Calculate bracket size (next power of 2)
                bracket_size = 2
                while len(players) > bracket_size:
                    bracket_size *= 2
                
                # Get tournament players
                t_players = list(TournamentPlayer.objects.filter(tournament=tournament))
                
                # Fill null seeds
                t_players = fill_null_seeds(t_players, bracket_size)
                
                # Get seeding order
                match_order = seeding_order(bracket_size)
                
                # Fit players into bracket
                sorted_players = fit_players_in_bracket(t_players, match_order)
                sorted_players = sorted_players[::-1]
                
                # Create tournament matches
                matches = []
                next_round_matches = []
                round_number = 1
                match_number = 1
                
                # First round
                while len(sorted_players) >= 2:
                    p1, p2 = sorted_players.pop(), sorted_players.pop()
                    
                    p1_user = None if not p1 else p1.user
                    p2_user = None if not p2 else p2.user
                    
                    # Create match
                    match = Match.objects.create(
                        community_id=community,
                        home1=p1_user,
                        away1=p2_user,
                    )
                    
                    # Create tournament match
                    tournament_match = TournamentMatch.objects.create(
                        match=match,
                        tournament=tournament,
                        match_number=match_number,
                        round=round_number
                    )
                    
                    matches.append(tournament_match)
                    next_round_matches.append(tournament_match)
                    match_number += 1
                
                # Subsequent rounds
                while len(next_round_matches) > 1:
                    current_round_matches = next_round_matches
                    next_round_matches = []
                    round_number += 1
                    match_number = 1
                    
                    while len(current_round_matches) >= 2:
                        current_round_matches = current_round_matches[::-1]
                        m1, m2 = current_round_matches.pop(), current_round_matches.pop()
                        
                        # Handle byes in second round
                        if round_number == 2:
                            m1_bye = None
                            m2_bye = None
                            
                            if not m1.match.home1:
                                m1_bye = m1.match.away1
                            elif not m1.match.away1:
                                m1_bye = m1.match.home1
                                
                            if not m2.match.home1:
                                m2_bye = m2.match.away1
                            elif not m2.match.away1:
                                m2_bye = m2.match.home1
                            
                            match = Match.objects.create(
                                home1=m1_bye,
                                away1=m2_bye,
                                community_id=community,
                            )
                        else:
                            match = Match.objects.create(
                                community_id=community,
                            )
                            
                        next_match = TournamentMatch.objects.create(
                            match=match,
                            tournament=tournament,
                            match_number=match_number,
                            round=round_number
                        )
                        
                        # Connect matches
                        m1.next_match = next_match
                        m1.save()
                        m2.next_match = next_match
                        m2.save()
                        
                        next_round_matches.append(next_match)
                        match_number += 1
                
                # Simulate some matches (first and second rounds)
                for t_match in matches[:int(len(matches)*0.75)]:
                    # Only simulate if both players exist
                    if t_match.match.home1 and t_match.match.away1:
                        # Simulate the match
                        simulate_tennis_match(t_match.match)
                        
                        # If this match has a next match, update it
                        if t_match.next_match:
                            if t_match.match.winner1:
                                # Put winner in next match
                                if random.choice([True, False]):  # Randomly choose home/away
                                    t_match.next_match.match.home1 = t_match.match.winner1
                                else:
                                    t_match.next_match.match.away1 = t_match.match.winner1
                                t_match.next_match.match.save()
                
        print(f"Created {len(tournaments)} tournaments with brackets")
        
    print("Database populated successfully!")

if __name__ == "__main__":
    run()