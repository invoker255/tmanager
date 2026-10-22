from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'priority', 'category', 'deadline', 'reminder_sent')
    list_filter = ('status', 'priority', 'category', 'reminder_sent')
    search_fields = ('title', 'description', 'user__username', 'user__email')