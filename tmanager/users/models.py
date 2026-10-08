from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class User(AbstractUser):
    username = models.CharField(unique=True, max_length=255, default='')
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    objects = UserManager()


class UserSettings(models.Model):
    REMINDER_CHOICES = [
        (12, 'Twelve hours before a deadline'),
        (24, 'Twenty four hours before a deadline'),
        (72, 'Seventy two hours before a deadline'),
        (0, 'Reminders are disabled'),
    ]

    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_settings'
    )
    reminder_hours_before = models.IntegerField(choices=REMINDER_CHOICES, default=24)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='dark')

    def __str__(self):
        return f'{self.user.username} settings'