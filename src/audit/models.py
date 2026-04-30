from django.conf import settings
from django.db import models

from users.models import Organization


class AuditActionType(models.TextChoices):
    LOGIN = 'login', 'Вхід'
    LOGOUT = 'logout', 'Вихід'
    CREATE = 'create', 'Створення'
    UPDATE = 'update', 'Оновлення'
    DELETE = 'delete', 'Видалення'
    CHANGE_STATUS = 'change_status', 'Зміна статусу'
    ASSIGN_ROLE = 'assign_role', 'Призначення ролі'


class AuditEntityType(models.TextChoices):
    USER = 'user', 'Користувач'
    CLIENT = 'client', 'Клієнт'
    SERVICE = 'service', 'Послуга'
    APPOINTMENT = 'appointment', 'Запис'
    AUTH = 'auth', 'Автентифікація'


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    action_type = models.CharField(max_length=30, choices=AuditActionType.choices)
    entity_type = models.CharField(max_length=30, choices=AuditEntityType.choices)
    entity_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Запис аудиту'
        verbose_name_plural = 'Журнал аудиту'
        indexes = [
            models.Index(fields=['organization', '-created_at'], name='audit_org_created_idx'),
            models.Index(fields=['organization', 'user', '-created_at'], name='audit_org_user_idx'),
            models.Index(
                fields=['organization', 'action_type', '-created_at'],
                name='audit_org_action_idx',
            ),
            models.Index(
                fields=['organization', 'entity_type', '-created_at'],
                name='audit_org_entity_idx',
            ),
        ]

    def __str__(self):
        return f'{self.action_type} - {self.entity_type} - {self.created_at:%Y-%m-%d %H:%M:%S}'
