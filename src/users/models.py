from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Адміністратор'
    MANAGER = 'manager', 'Менеджер'
    EMPLOYEE = 'employee', 'Співробітник'


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.EMPLOYEE
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"