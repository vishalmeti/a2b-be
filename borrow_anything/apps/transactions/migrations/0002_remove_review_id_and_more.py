# Generated by Django 5.1.7 on 2025-03-30 18:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='review',
            name='id',
        ),
        migrations.AlterField(
            model_name='review',
            name='borrower_review_submitted_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp when borrower submitted their part', null=True),
        ),
        migrations.AlterField(
            model_name='review',
            name='borrowing_request',
            field=models.OneToOneField(help_text='The completed borrowing request being reviewed', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='review', serialize=False, to='transactions.borrowingrequest'),
        ),
        migrations.AlterField(
            model_name='review',
            name='lender_review_submitted_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp when lender submitted their part', null=True),
        ),
    ]
