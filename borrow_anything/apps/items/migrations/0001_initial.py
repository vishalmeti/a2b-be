# Generated by Django 5.1.7 on 2025-03-30 05:27

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('communities', '0001_initial'),
        ('users', '0003_userprofile_profile_picture_s3_key'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(blank=True, help_text='Optional icon class (e.g., Font Awesome)', max_length=50, null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Controls visibility of the category')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('condition', models.CharField(choices=[('NEW', 'New'), ('LIKE_NEW', 'Like New'), ('GOOD', 'Good'), ('FAIR', 'Fair'), ('POOR', 'Poor')], default='GOOD', max_length=10)),
                ('availability_status', models.CharField(choices=[('AVAILABLE', 'Available'), ('BORROWED', 'Currently Borrowed'), ('UNAVAILABLE', 'Temporarily Unavailable')], db_index=True, default='AVAILABLE', max_length=15)),
                ('availability_notes', models.TextField(blank=True, help_text="e.g., 'Weekends only', 'Msg me before requesting'")),
                ('deposit_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=8, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('borrowing_fee', models.DecimalField(decimal_places=2, default=0.0, max_digits=6, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('max_borrow_duration_days', models.PositiveIntegerField(blank=True, help_text='Max days per borrow (optional)', null=True)),
                ('pickup_details', models.TextField(blank=True, help_text="Default pickup instructions (e.g., 'Lobby pickup')")),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='Set to False to hide/soft-delete')),
                ('average_item_rating', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1.0), django.core.validators.MaxValueValidator(5.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='items.category')),
                ('community', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='community_items', to='communities.community')),
                ('owner_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_items', to='users.userprofile')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ItemImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('s3_key', models.CharField(help_text='S3 object key for the item image', max_length=1024)),
                ('caption', models.CharField(blank=True, max_length=100)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='items.item')),
            ],
            options={
                'ordering': ['uploaded_at'],
            },
        ),
    ]
