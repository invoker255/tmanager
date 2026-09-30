from django.db import models
from django.conf import settings

class UserSettings(models.Model):
    REMINDER_CHOICES = [
        (12, 'Twelve hours before a deadline'),
        (24, 'Twenty four hours before a deadline'),
        (72, 'Seventy two hours before a deadline'),
        (0, 'Reminder are disabled'),
    ]

    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_settings')
    reminder_hours_before = models.IntegerField(choices=REMINDER_CHOICES, default=24)
    theme = models.CharField(choices=THEME_CHOICES, default='dark')

    def __str__(self):
        return f'{self.user.username} settings'