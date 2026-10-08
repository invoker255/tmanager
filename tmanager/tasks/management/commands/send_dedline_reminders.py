from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings


def send_deadline_reminder_email(user, task):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    link = f"{settings.FRONTEND_URL}/tasks/{task.id}"

    html_content = render_to_string(
        "gmail/deadline_reminder.html", {
            'user': user,
            'task': task,
            'link': link,
        })

    email = EmailMessage(
        f"Reminder: task deadline «{task.title}»",
        html_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.content_subtype = 'html'
    email.send(fail_silently=False)