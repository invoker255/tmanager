from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tasks.emails import send_deadline_reminder_email
from tasks.models import Task


class Command(BaseCommand):
    help = 'Sending deadline reminders'

    def handle(self, *args, **options):
        now = timezone.now()
        tasks = (
            Task.objects
            .select_related('user', 'user__user_settings')
            .filter(reminder_sent=False, deadline__gt=now, user__is_email_verified=True)
            .exclude(status='done')
        )
        sent = 0
        for task in tasks:
            user_settings = getattr(task.user, 'user_settings', None)
            hours = user_settings.reminder_hours_before if user_settings else 24
            if hours == 0:
                continue
            if task.deadline - now > timedelta(hours=hours):
                continue
            try:
                send_deadline_reminder_email(task.user, task)
            except Exception as exc:
                self.stderr.write(f'Задача {task.id}: {exc}')
                continue
            task.reminder_sent = True
            task.save(update_fields=['reminder_sent'])
            sent += 1
        self.stdout.write(f'Reminders sent: {sent}')