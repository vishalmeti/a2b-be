from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "community", "phone_number", "is_community_member_verified")
    search_fields = ("user__username", "phone_number", "community__name")
    list_filter = ("is_community_member_verified", "community")
