from django.db import models
from community.models import Community
from django.conf import settings

from users.models import UserProfile

class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    community_id = models.ForeignKey(Community, on_delete=models.SET_NULL, null=True, blank=True, related_name="matches")
    match_date = models.DateTimeField(null = True, blank = True)

    home1 = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="home1_matches", null=True, blank=True)
    home2 = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="home2_matches", null=True, blank=True)
    away1 = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="away1_matches", null=True, blank=True)
    away2 = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="away2_matches", null=True, blank=True)

    winner1 = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name="match_winner1", blank=True)
    winner2 = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name="match_winner2", blank=True)
    max_sets = models.IntegerField(default=3)
    match_tiebreak = models.BooleanField(default=False)
    ad = models.BooleanField(default=True)

    def __str__(self):
        if self.home2:
            return f"{self.home1} & {self.home2} vs {self.away1} & {self.away2}"
        else:
            return f"{self.home1} vs {self.away1}"
        
class MatchMoment(models.Model):
    match_moment_id = models.BigAutoField(primary_key=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="moments")
    timestamp = models.DateTimeField(auto_now_add=True)
    current_game_home = models.BigIntegerField()
    current_game_away = models.BigIntegerField()
    current_set_home = models.BigIntegerField()
    current_set_away = models.BigIntegerField()
    match_score_home = models.BigIntegerField()
    match_score_away = models.BigIntegerField()

    def __str__(self):
        return f"Moment {self.match_moment_id} - Match {self.match.match_id}"


class MatchSet(models.Model):
    match_moment = models.ForeignKey(MatchMoment, on_delete=models.CASCADE, related_name="sets")
    set_number = models.BigIntegerField()
    home_games = models.BigIntegerField()
    away_games = models.BigIntegerField()

    class Meta:
        unique_together = ("match_moment", "set_number")  # Evita sets duplicados para o mesmo momento

    def __str__(self):
        return f"Set {self.set_number} - MatchMoment {self.match_moment.match_moment_id}"
