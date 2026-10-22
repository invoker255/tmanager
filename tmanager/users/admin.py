from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserSettings


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_email_verified', 'is_staff', 'date_joined')
    list_filter = ('is_email_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    fieldsets = UserAdmin.fieldsets + (('Email verification', {'fields': ('is_email_verified',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {'fields': ('email',)}),)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'reminder_hours_before', 'theme')