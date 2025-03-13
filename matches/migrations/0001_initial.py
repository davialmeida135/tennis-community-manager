# Generated by Django 5.1.7 on 2025-03-13 19:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("community", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Match",
            fields=[
                ("match_id", models.AutoField(primary_key=True, serialize=False)),
                ("match_date", models.DateTimeField(blank=True, null=True)),
                ("max_sets", models.IntegerField(default=3)),
                ("match_tiebreak", models.BooleanField(default=False)),
                ("ad", models.BooleanField(default=True)),
                (
                    "away1",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="away1_matches",
                        to="users.userprofile",
                    ),
                ),
                (
                    "away2",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="away2_matches",
                        to="users.userprofile",
                    ),
                ),
                (
                    "community_id",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="matches",
                        to="community.community",
                    ),
                ),
                (
                    "home1",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="home1_matches",
                        to="users.userprofile",
                    ),
                ),
                (
                    "home2",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="home2_matches",
                        to="users.userprofile",
                    ),
                ),
                (
                    "winner1",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="match_winner1",
                        to="users.userprofile",
                    ),
                ),
                (
                    "winner2",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="match_winner2",
                        to="users.userprofile",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MatchMoment",
            fields=[
                (
                    "match_moment_id",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("current_game_home", models.TextField()),
                ("current_game_away", models.TextField()),
                ("current_set_home", models.BigIntegerField()),
                ("current_set_away", models.BigIntegerField()),
                ("match_score_home", models.BigIntegerField()),
                ("match_score_away", models.BigIntegerField()),
                (
                    "match",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="moments",
                        to="matches.match",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MatchSet",
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
                ("set_number", models.BigIntegerField()),
                ("home_games", models.BigIntegerField()),
                ("away_games", models.BigIntegerField()),
                (
                    "match_moment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sets",
                        to="matches.matchmoment",
                    ),
                ),
            ],
            options={
                "unique_together": {("match_moment", "set_number")},
            },
        ),
    ]
