from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import Tournament, TournamentPlayer, TournamentMatch
from scoreboard.models import Match
from .serializers import TournamentSerializer, TournamentPlayerSerializer, TournamentMatchSerializer
import random
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
                        elif not m1.match.away1:
                            m1_bye = m1.match.home1
                        if not m2.match.home1:
                            m2_bye = m2.match.away1
                        elif not m2.match.away1:
                            m2_bye = m2.match.home1
                        
                        match = Match.objects.create(
                                home1 = m1_bye,
                                away1 = m2_bye,
                                community_id=tournament.community_id,
                            )
                    else:
                        match = Match.objects.create(
                            community_id=tournament.community_id,
                        )
        
                    next_match = TournamentMatch.objects.create(
                        match=match,
                        tournament=tournament,
                        match_number=match_number,
                        round=round_number
                    )

                    # Conectar partidas anteriores com a próxima
                    m1.next_match = next_match
                    m1.save()
                    m2.next_match = next_match
                    m2.save()

                    next_round_matches.append(next_match)
                    match_number += 1

        return Response({"message": "Bracket gerado com sucesso"}, status=status.HTTP_201_CREATED)


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
