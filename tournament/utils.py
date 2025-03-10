import random
def seeding_order(n):
    """
    Constrói recursivamente a ordem do bracket para n jogadores (n é potência de 2).
    Para n == 2, retorna [1, 2].
    Para n maior, retorna a ordem que garante que os seeds mais altos se encontrem por último.
    """
    if n == 2:
        return [1, 2]
    previous = seeding_order(n // 2)
    bracket = []
    for seed in previous:
        bracket.append(seed)
        bracket.append(n + 1 - seed)
    return bracket

def fill_null_seeds(players, bracket_size):
    """
    Preenche os seeds nulos dos jogadores restantes.
    """
    seed = 1
    available_seeds = list(range(1, len(players) + 1))
    for player in players:
        if player.seed is not None:
            available_seeds.remove(player.seed)

    random.shuffle(available_seeds)
    for player in players:
        if player.seed is None:
            player.seed = available_seeds.pop()
            player.save()
    
    return players

def fit_players_in_bracket(players, bracket_order):
    """
    Ajusta a ordem dos jogadores para se encaixar na ordem do bracket.
    Identifica seeds faltantes e os preenche com jogadores nulos.
    """
    players_by_seed = {player.seed: player for player in players}
    sorted_players = []
    for seed in bracket_order:
        player = players_by_seed.get(seed)
        if player:
            sorted_players.append(player)
        else:
            sorted_players.append(None)
    
    return sorted_players