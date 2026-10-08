from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def send_deadline_reminder_email(user, task):
    link = f'{settings.FRONTEND_URL}/tasks/{task.id}'
    html_content = render_to_string(
        'gmail/deadline_reminder.html',
        {'user': user, 'task': task, 'link': link}
    )
    email = EmailMessage(
        f'Reminder: task deadline «{task.title}»',
        html_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)