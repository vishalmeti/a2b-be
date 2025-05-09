# Generated by Django 5.1.7 on 2025-04-27 09:34

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_usercommunitymembership'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='average_rating',
            field=models.FloatField(default=0.0, help_text='Average rating received by the user (0-5)', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(5.0)]),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='rating_count',
            field=models.PositiveIntegerField(default=0, help_text='Total number of ratings received'),
        ),
    ]
