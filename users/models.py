from django.db import models
from django.contrib.auth.models import  AbstractUser
# Create your models here.

class UserInfo(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('editor', 'Editor'),
    )
    name = models.CharField(max_length=30, blank=True)
    roles = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')