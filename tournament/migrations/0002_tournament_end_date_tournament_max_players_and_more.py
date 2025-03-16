# Generated by Django 5.1.7 on 2025-03-16 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tournament", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="tournament",
            name="end_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tournament",
            name="max_players",
            field=models.IntegerField(default=32, null=True),
        ),
        migrations.AddField(
            model_name="tournament",
            name="prize",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="tournament",
            name="rules",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tournament",
            name="start_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tournament",
            name="started",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="tournament",
            name="subscription_fee",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="tournament",
            name="subscription_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tournament",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
