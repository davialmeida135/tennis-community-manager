from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import Tournament, TournamentPlayer, TournamentMatch
from users.models import UserProfile
from matches.models import Match
from .serializers import TournamentPlayerSerializer, TournamentSerializer, TournamentMatchSerializer
from .utils import seeding_order, fill_null_seeds, fit_players_in_bracket

class TournamentViewSet(viewsets.ModelViewSet):
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer

    @action(detail=True, methods=["post"])
    def generate_bracket(self, request, pk=None):
        """
        Gera partidas para um torneio de eliminação única.
        """
        tournament: Tournament = self.get_object()
        players = list(TournamentPlayer.objects.filter(tournament=tournament))

        if len(players) < 2:
            return Response({"error": "Pelo menos 2 jogadores são necessários"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove todas as partidas existentes deste torneio antes de gerar o novo bracket
        TournamentMatch.objects.filter(tournament=tournament).delete()

        # Garantir que o número máximo de jogadores seja uma potência de 2
        bracket_size = 2
        while len(players) > bracket_size:
            bracket_size *= 2

        # Lista com ordem de seeds para o bracket
        match_order = seeding_order(bracket_size)
        
        # Preencher jogadores sem seed
        players = fill_null_seeds(players, bracket_size)

        # Ordenar jogadores de acordo com a ordem de seeds
        players = fit_players_in_bracket(players, match_order)

        players = players[::-1]  # Inverter a ordem para que o seed 1 seja o último

        with transaction.atomic():
            matches = []
            next_round_matches = []
            round_number = 1
            match_number = 1

            # Criando a primeira rodada
            while len(players) >= 2:
                p1, p2 = players.pop(), players.pop()

                if not p1:
                    p1_user = None
                else:
                    p1_user = p1.user
                if not p2:
                    p2_user = None
                else:
                    p2_user = p2.user

                match = Match.objects.create(
                    community_id=tournament.community_id,
                    home1=p1_user,
                    away1=p2_user,
                )

                tournament_match = TournamentMatch.objects.create(
                    match=match,
                    tournament=tournament,
                    match_number=match_number,
                    round=round_number
                )
                matches.append(tournament_match)
                next_round_matches.append(tournament_match)
                match_number += 1

            # Criando rodadas subsequentes
            while len(next_round_matches) > 1:
                current_round_matches: list[TournamentMatch] = next_round_matches
                next_round_matches = []
                round_number += 1
                match_number = 1

                while len(current_round_matches) >= 2:
                    current_round_matches = current_round_matches[::-1]
                    m1, m2 = current_round_matches.pop(), current_round_matches.pop()
                        
                    if round_number == 2:
                        m1_bye = None
                        m2_bye = None
                        if not m1.match.home1:
                            m1_bye = m1.match.away1
                            m1.match.winner1 = m1_bye
                            m1.match.save()
                        elif not m1.match.away1:
                            m1_bye = m1.match.home1
                            m1.match.winner1 = m1_bye
                            m1.match.save()
                        if not m2.match.home1:
                            m2_bye = m2.match.away1
                            m2.match.winner1 = m2_bye
                            m2.match.save()
                        elif not m2.match.away1:
                            m2_bye = m2.match.home1
                            m2.match.winner1 = m2_bye
                            m2.match.save()
                        
                        match = Match.objects.create(
                                home1 = m1_bye,
                                away1 = m2_bye,
                                community_id=tournament.community_id,
                            )
                    else:
                        match = Match.objects.create(
                            community_id=tournament.community_id,
                        )
        
                    next_tournament_match = TournamentMatch.objects.create(
                        match=match,
                        tournament=tournament,
                        match_number=match_number,
                        round=round_number
                    )

                    # Conectar partidas anteriores com a próxima
                    m1.next_match = match
                    m1.save()
                    m2.next_match = match
                    m2.save()

                    next_round_matches.append(next_tournament_match)
                    match_number += 1

        return Response({"message": "Bracket gerado com sucesso"}, status=status.HTTP_201_CREATED)

    # TODO Checagens de permissão/validação
    @action(detail=True, methods=["get"])
    def players(self, request, pk=None):
        """
        Retorna todos os jogadores inscritos em um torneio.
        """
        tournament = self.get_object()
        players = TournamentPlayer.objects.filter(tournament=tournament)
        serializer = TournamentPlayerSerializer(players, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="players/(?P<player_id>[^/.]+)")
    def player_detail(self, request, pk=None, player_id=None):
        """
        Retorna os detalhes de um jogador específico do torneio.
        """
        tournament = self.get_object()
        
        try:
            player = UserProfile.objects.get(id=player_id)
            player = TournamentPlayer.objects.get(tournament=tournament, user=player)
            serializer = TournamentPlayerSerializer(player)
            return Response(serializer.data)
        except TournamentPlayer.DoesNotExist:
            return Response({"error": "Player not found in tournament"}, status=status.HTTP_404_NOT_FOUND)    
    
    # TODO Checagens de permissão/validação/torneio ja iniciou
    @action(detail=True, methods=["post"])
    def add_player(self, request, pk=None):
        """
        Adiciona um jogador a um torneio.
        """
        tournament = self.get_object()
        action_user = request.user
        user_id = request.data.get("user_id")
        print(f"User {action_user} is trying to add user {user_id} to tournament {pk}")

        if TournamentPlayer.objects.filter(tournament=tournament, user=user_id).exists():
            return Response({"error": "O jogador já está inscrito no torneio"}, status=status.HTTP_400_BAD_REQUEST)

        user = UserProfile.objects.get(pk=user_id)
        player = TournamentPlayer.objects.create(tournament=tournament, user=user)
        serializer = TournamentPlayerSerializer(player)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=["post"])
    def remove_player(self, request, pk=None):
        """
        Remove um jogador de um torneio.
        """
        tournament = self.get_object()
        action_user = request.user
        user_id = request.data.get("user_id")
        print(f"User {action_user} is trying to remove user {user_id} from tournament {pk}")

        player = TournamentPlayer.objects.filter(tournament=tournament, user=user_id)
        if not player.exists():
            return Response({"error": "O jogador não está inscrito no torneio"}, status=status.HTTP_400_BAD_REQUEST)

        player.delete()
        return Response({"message": "Jogador removido com sucesso"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def matches(self, request, pk=None):
        """
        Retorna todas as partidas de um torneio.
        """
        tournament = self.get_object()
        matches = TournamentMatch.objects.filter(tournament=tournament)
        serializer = TournamentMatchSerializer(matches, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="matches/(?P<match_id>[^/.]+)")
    def match_detail(self, request, pk=None, match_id=None):
        """
        Retorna os detalhes de uma partida específica do torneio.
        """
        tournament = self.get_object()
        
        try:
            match = Match.objects.get(match_id=match_id)
            match = TournamentMatch.objects.get(match=match)
            serializer = TournamentMatchSerializer(match)
            return Response(serializer.data)
        except TournamentMatch.DoesNotExist:
            return Response({"error": "Match not found in tournament"}, status=status.HTTP_404_NOT_FOUND)
    
    

class TournamentPlayerViewSet(viewsets.ModelViewSet):
    queryset = TournamentPlayer.objects.all()
    serializer_class = TournamentPlayerSerializer


class TournamentMatchViewSet(viewsets.ModelViewSet):
    queryset = TournamentMatch.objects.all()
    serializer_class = TournamentMatchSerializer

    def update(self, request, *args, **kwargs):
        """Permite atualizar o next_match de uma partida"""
        instance = self.get_object()
        next_match_id = request.data.get("next_match_id")

        if next_match_id:
            try:
                next_match = TournamentMatch.objects.get(pk=next_match_id, tournament=instance.tournament)
                instance.next_match = next_match
                instance.save()
            except TournamentMatch.DoesNotExist:
                return Response({"error": "Próxima partida não encontrada ou não pertence ao mesmo torneio"}, status=400)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
