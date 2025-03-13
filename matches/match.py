import copy
from datetime import datetime
import json
class TennisMatch:
    def __init__(self, home1: str, away1: str, ownerUsername= None, match_id=None, best_of=3, game_goal=6, ad= True):
        self.match_id = match_id
        self.home1 = home1
        self.away1 = away1
        self.match_moment = MatchMoment()
        self.ownerUsername = ownerUsername
        self.history_undo = []
        self.history_redo = []
        self.best_of = best_of
        self.game_goal = game_goal
        self.ad = ad
        self.title = f"{home1} x {away1} : {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    def to_dict(self):
        return {
            'idMatch': self.match_id,
            'title': self.title,
            'home1': self.home1,
            'away1': self.away1,
            'ownerUsername': self.ownerUsername,  
            'moments': [self.match_moment.to_dict()],
            
        }

    def to_json(self):
        return json.dumps(self.to_dict(), sort_keys=True, indent=4)

    @classmethod
    def from_dict(cls, data):
        match = cls(data['home1'], data['away1'], match_id=data['idMatch'])
        if 'ownerUsername' in data:
            match.ownerUsername = data['ownerUsername']
        match.match_moment = MatchMoment.from_dict(data['moments'][0])
        match.title = data['title']
        return match

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls.from_dict(data)

    def start_match(self):
        self.match_moment.current_set = Set()
        self.match_moment.current_game = Game()

    def end_match(self):
        # Perform any necessary cleanup or calculations
        pass

    def point(self, player):
        self.history_undo.append(copy.deepcopy(self.match_moment))
        self.history_redo = []
        if isinstance(self.match_moment.current_game, Tiebreak):
            self.update_tiebreak(player)
        elif isinstance(self.match_moment.current_game, Game):
            self.update_game(player)

    def update_game(self, player):
        if player == self.home1:
            if self.match_moment.current_game.home1_score == '0':
                self.match_moment.current_game.home1_score = '15'
            elif self.match_moment.current_game.home1_score == '15':
                self.match_moment.current_game.home1_score = '30'
            elif self.match_moment.current_game.home1_score == '30':
                self.match_moment.current_game.home1_score = '40'
            elif self.match_moment.current_game.home1_score == '40' and self.match_moment.current_game.away1_score in ['0', '15', '30']:
                self.update_set(player)
            elif self.match_moment.current_game.home1_score == '40' and self.match_moment.current_game.away1_score == '40':
                self.match_moment.current_game.home1_score = 'AD'
            elif self.match_moment.current_game.home1_score == 'AD':
                self.update_set(player)
            elif self.match_moment.current_game.away1_score == 'AD':
                self.match_moment.current_game.home1_score = '40'
                self.match_moment.current_game.away1_score = '40'

        if player == self.away1:
            if self.match_moment.current_game.away1_score == '0':
                self.match_moment.current_game.away1_score = '15'
            elif self.match_moment.current_game.away1_score == '15':
                self.match_moment.current_game.away1_score = '30'
            elif self.match_moment.current_game.away1_score == '30':
                self.match_moment.current_game.away1_score = '40'
            elif self.match_moment.current_game.away1_score == '40' and self.match_moment.current_game.home1_score in ['0', '15', '30']:
                self.update_set(player)
            elif self.match_moment.current_game.away1_score == '40' and self.match_moment.current_game.home1_score == '40':
                self.match_moment.current_game.away1_score = 'AD'
            elif self.match_moment.current_game.away1_score == 'AD':
                self.update_set(player)
            elif self.match_moment.current_game.home1_score == 'AD':
                self.match_moment.current_game.home1_score = '40'
                self.match_moment.current_game.away1_score = '40'

    def update_set(self, player):
        if player == self.home1:
            self.match_moment.current_set.home1_score += 1
            self.match_moment.current_game = Game()
            # Win by 2 games or more
            if self.match_moment.current_set.home1_score >= self.game_goal and self.match_moment.current_set.home1_score - self.match_moment.current_set.away1_score >= 2:
                self.match_moment.sets.append(self.match_moment.current_set)
                self.match_moment.current_set = Set()
                self.match_moment.current_game = Game()
                self.match_moment.match_score_h1 += 1
            # Win 7-6
            elif self.match_moment.current_set.home1_score == self.game_goal + 1:
                self.match_moment.sets.append(self.match_moment.current_set)
                self.match_moment.current_set = Set()
                self.match_moment.current_game = Game()
                self.match_moment.match_score_h1 += 1       
        if player == self.away1:
            self.match_moment.current_set.away1_score += 1
            self.match_moment.current_game = Game()
            # Win by 2 games or more
            if self.match_moment.current_set.away1_score >= self.game_goal and self.match_moment.current_set.away1_score - self.match_moment.current_set.home1_score >= 2:
                self.match_moment.sets.append(self.match_moment.current_set)
                self.match_moment.current_set = Set()
                self.match_moment.match_score_a1 += 1
            # Win 7-6
            elif self.match_moment.current_set.away1_score == self.game_goal + 1:
                self.match_moment.sets.append(self.match_moment.current_set)
                self.match_moment.current_set = Set()
                self.match_moment.current_game = Game()
                self.match_moment.match_score_a1 += 1

        if self.match_moment.current_set.home1_score == self.game_goal and self.match_moment.current_set.away1_score == self.game_goal:
            self.match_moment.current_game = Tiebreak()

        if self.match_moment.match_score_h1 == self.best_of or self.match_moment.match_score_a1 == self.best_of:
            self.end_match()

    def update_tiebreak(self, player):
        if player == self.home1:
            self.match_moment.current_game.home1_score += 1
        if player == self.away1:
            self.match_moment.current_game.away1_score += 1

        if self.match_moment.current_game.home1_score >= self.match_moment.current_game.max_score and self.match_moment.current_game.home1_score - self.match_moment.current_game.away1_score >= self.match_moment.current_game.min_difference:
            self.update_set(self.home1)
        elif self.match_moment.current_game.away1_score >= self.match_moment.current_game.max_score and self.match_moment.current_game.away1_score - self.match_moment.current_game.home1_score >= self.match_moment.current_game.min_difference:
            self.update_set(self.away1)

    def update_history(self):
        self.history_undo.append(self.match_moment)

    def undo(self):
        if len(self.history_undo) > 0:
            self.history_redo.append(copy.deepcopy(self.match_moment))
            self.match_moment = self.history_undo.pop()
            return
        return

    def redo(self):
        if len(self.history_redo) > 0:
            self.history_undo.append(copy.deepcopy(self.match_moment))
            self.match_moment = self.history_redo.pop()
            return
        return

    def relatorio(self):
        #print("Match id: ", self.match_id)
        #print("Player 1: ", self.home1)
        #print("Player 2: ", self.away1)

        for set in range(len(self.match_moment.sets)):
            #print(str(set) + " set : ")
            self.match_moment.sets[set].print_scores()
        #print("Current Set: ")
        self.match_moment.current_set.print_scores()
        #print("Current game: ")
        self.match_moment.current_game.print_scores()

class MatchMoment:
    def __init__(self):
        self.idMatch=None
        self.idMatchMoment=None
        self.sets = []
        self.current_set: Set = None
        self.current_game = None
        self.current_game_h1 = '0'
        self.current_game_a1 = '0'
        self.current_set_h1 = 0
        self.current_set_a1 = 0
        self.match_score_h1 = 0
        self.match_score_a1 = 0

    def to_dict(self):
        return {
            'idMatch': self.idMatch,
            'idMatchMoment': self.idMatchMoment,
            'current_game_h1': self.current_game.home1_score,
            'current_game_a1': self.current_game.away1_score,
            'current_set_h1': self.current_set.home1_score,
            'current_set_a1': self.current_set.away1_score,
            'match_score_h1': self.match_score_h1,
            'match_score_a1': self.match_score_a1,
            'sets': [set.to_dict() for set in self.sets],
        }

    @classmethod
    def from_dict(cls, data):
        moment = cls()
        if 'idMatch' in data:
            moment.idMatch = data['idMatch']
        if 'idMatchMoment' in data:
            moment.idMatchMoment = data['idMatchMoment']

        moment.sets = [Set.from_dict(set) for set in data['sets']]
        moment.current_set = Set.from_dict(data)
        moment.match_score_h1 = int(data['match_score_h1'])
        moment.match_score_a1 = int(data['match_score_a1'])

        if moment.current_set.home1_score == 6 and moment.current_set.away1_score == 6:
            moment.current_game = Tiebreak.from_dict(data)
        else:
            moment.current_game = Game.from_dict(data)

        return moment

class Set:
    def __init__(self):
        self.idMatchMoment=None
        self.idMatchSet = None
        self.home1_score = 0
        self.away1_score = 0

    def print_scores(self):
        print("(Set)Home Player Score:", self.home1_score)
        print("(Set)Away Player Score:", self.away1_score)

    def to_dict(self):
        return {
            'idMatchMoment': self.idMatchMoment,
            'idMatchSet': self.idMatchSet,
            'h1': self.home1_score,
            'a1': self.away1_score,
        }

    @classmethod
    def from_dict(cls, data):
        set = cls()
        if 'idMatchMoment' in data:
            set.idMatchMoment = data['idMatchMoment']
        if 'idMatchSet' in data:
            set.idMatchSet = data['idMatchSet']
        if 'h1' in data and 'a1' in data:
            set.home1_score = int(data['h1'])
            set.away1_score = int(data['a1'])
        elif 'current_set_h1' in data and 'current_set_a1' in data:
            set.home1_score = int(data['current_set_h1'])
            set.away1_score = int(data['current_set_a1'])
        return set

class Game:
    def __init__(self):
        self.home1_score = '0'
        self.away1_score = '0'

    def print_scores(self):
        print("(Game)Player 1 Score no game:", self.home1_score)
        print("(Game)Player 2 Score no game:", self.away1_score)

    def to_dict(self):
        return {
            'current_game_h1': self.home1_score,
            'current_game_a1': self.away1_score,
        }

    @classmethod
    def from_dict(cls, data):
        game = cls()
        game.home1_score = data['current_game_h1']
        game.away1_score = data['current_game_a1']
        return game

class Tiebreak:
    def __init__(self, max_score=7, min_difference=2):
        self.id=None
        self.home1_score = 0
        self.away1_score = 0
        self.max_score = max_score
        self.min_difference = min_difference

    def print_scores(self):
        print("(Tiebreak)Player 1 Score:", self.home1_score)
        print("(Tiebreak)Player 2 Score:", self.away1_score)

    def to_dict(self):
        return {
            'current_game_h1': self.home1_score,
            'current_game_a1': self.away1_score,
        }

    @classmethod
    def from_dict(cls, data):
        game = cls()
        game.home1_score = int(data['current_game_h1'])
        game.away1_score = int(data['current_game_a1'])
        return game
    
if __name__ == '__main__':
    # Example usage
    p = TennisMatch('Davi', 'Gustavo', 13)
    p.start_match()

    for i in range(20):
        p.point('Davi')
    for i in range(24):
        p.point('Gustavo')
    for i in range(6):
        p.point('Davi')
    #p.point('Gustavo')

    p.relatorio()
    print("==========================================")
    print(p.to_json())
    print("==========================================")

    q = TennisMatch.from_json("""
    {
    "idMatch": 7,
        "moments": [
            {"current_game_h1": "40",
            "current_game_a1": "30",
            "current_set_h1": 0, 
            "current_set_a1": 1, 
            "idMatch": 7, 
            "idMatchMoment": 3, 
            "match_score_h1": 1, 
            "match_score_a1": 2, 
            "sets": 
                [
                {"idMatchMoment": 3, 
                "idMatchSet": 9, 
                "h1": 7, "a1": 6}, 
                {"idMatchMoment": 3, 
                "idMatchSet": 10, 
                "h1": 4, "a1": 6}, 
                {"idMatchMoment": 3, 
                "idMatchSet": 11, 
                "h1": 6, 
                "a1": 3},
                {"idMatchMoment": 3, 
                "h1": 6, 
                "a1": 1}
                ]
            }
        ], 
        "ownerUsername": "Rafael", 
        "home1": "Jonas", 
        "away1": "Bob", 
        "title": 
        " Alice vs Boooo"
    }

    """)
    """q.relatorio()
    q.point('Jonas')
    q.relatorio()
    #print(q.to_json())"""