from django.db import models
from django.conf import settings

class Task(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE,
                             related_name='tasks')

    STATUS_CHOICES = [
        ('todo', 'Нужно Сделать'),
        ('in_progress', 'В процессе'),
        ('done', 'Готово'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]



    CATEGORY_CHOICES = [
        ('Work', 'Работа'),
        ('Personal', 'Личное')
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES, default='Personal')

    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(null=True, blank=True)
    reminder_sent=models.BooleanField(default=False)
    def __str__(self):
        return self.title

# Create your models here.
