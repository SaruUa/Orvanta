from django.conf import settings
from django.db import models

from users.models import Organization


class Client(models.Model):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_clients',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Клієнт'
        verbose_name_plural = 'Клієнти'
        indexes = [
            models.Index(fields=['organization', 'is_active'], name='client_org_active_idx'),
            models.Index(fields=['organization', 'full_name'], name='client_org_name_idx'),
        ]

    def __str__(self):
        return self.full_name
