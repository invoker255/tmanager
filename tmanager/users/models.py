from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager


class User(AbstractUser):
    username = models.CharField(unique=True, max_length=255, default='')
    email = models.EmailField(unique=True)

    objects = UserManager()
# Create your models here.
