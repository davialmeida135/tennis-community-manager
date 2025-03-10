# Generated by Django 5.1.7 on 2025-03-08 21:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("community", "0001_initial"),
        ("scoreboard", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tournament",
            fields=[
                ("tournament_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("single_elimination", "Single Elimination"),
                            ("double_elimination", "Double Elimination"),
                        ],
                        max_length=50,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "community_id",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tournaments",
                        to="community.community",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TournamentMatch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("round", models.IntegerField()),
                ("match_number", models.IntegerField()),
                (
                    "match",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tournament_match",
                        to="scoreboard.match",
                    ),
                ),
                (
                    "next_match",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="previous_match",
                        to="tournament.tournamentmatch",
                    ),
                ),
                (
                    "tournament",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matches",
                        to="tournament.tournament",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TournamentPlayer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("seed", models.IntegerField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("registered", "Registered"),
                            ("eliminated", "Eliminated"),
                            ("winner", "Winner"),
                            ("pending approval", "Pending Approval"),
                            ("pending payment", "Pending Payment"),
                        ],
                        default="registered",
                        max_length=20,
                    ),
                ),
                (
                    "tournament",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tournament_players",
                        to="tournament.tournament",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tournament_entries",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "unique_together": {("tournament", "user")},
            },
        ),
    ]
