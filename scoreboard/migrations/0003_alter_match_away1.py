# Generated by Django 5.1.7 on 2025-03-09 12:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scoreboard", "0002_alter_match_away1_alter_match_away2_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="match",
            name="away1",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="away1_matches",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
