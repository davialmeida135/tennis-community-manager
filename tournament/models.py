from django.db import models
from matches.models import Match
from community.models import Community
from users.models import UserProfile
from django.conf import settings

class Tournament(models.Model):
    tournament_id = models.AutoField(primary_key=True)
    community_id = models.ForeignKey(Community, on_delete=models.SET_NULL, related_name="tournaments", null=True, blank=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=[("single_elimination", "Single Elimination"), ("double_elimination", "Double Elimination")])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TournamentPlayer(models.Model):
    STATUS_CHOICES = [
        ("registered", "Registered"),
        ("eliminated", "Eliminated"),
        ("winner", "Winner"),
        ("pending approval", "Pending Approval"),
        ("pending payment", "Pending Payment"),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="tournament_players")
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="tournament_entries")
    seed = models.IntegerField(null=True, blank=True)  # Optional seeding
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="registered")

    class Meta:
        unique_together = ("tournament", "user")  # Prevent duplicate registrations

    def __str__(self):
        return f"{self.user.username} in {self.tournament.name}"


class TournamentMatch(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name="tournament_match")
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="matches")
    round = models.IntegerField()
    match_number = models.IntegerField()
    next_match = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="previous_match")

    def __str__(self):
        return f"Round {self.round} - Match {self.match_number}"
