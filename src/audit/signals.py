from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from appointments.models import Appointment
from clients.models import Client
from services_catalog.models import Service
from users.models import User

from .models import AuditActionType, AuditEntityType, AuditLog


_TRACKED_MODELS = {
    Client: AuditEntityType.CLIENT,
    Service: AuditEntityType.SERVICE,
    Appointment: AuditEntityType.APPOINTMENT,
    User: AuditEntityType.USER,
}


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        action_type=AuditActionType.LOGIN,
        entity_type=AuditEntityType.AUTH,
        entity_id=user.id,
        description=f"Користувач {user.username} виконав вхід до системи.",
        ip_address=get_client_ip(request),
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user is None:
        return

    AuditLog.objects.create(
        user=user,
        action_type=AuditActionType.LOGOUT,
        entity_type=AuditEntityType.AUTH,
        entity_id=user.id,
        description=f"Користувач {user.username} вийшов із системи.",
        ip_address=get_client_ip(request),
    )


def get_client_ip(request):
    if request is None:
        return None

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


@receiver(pre_save)
def cache_old_instance_state(sender, instance, **kwargs):
    if sender not in _TRACKED_MODELS:
        return

    if not instance.pk:
        instance._old_instance = None
        return

    try:
        instance._old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._old_instance = None


@receiver(post_save)
def log_model_save(sender, instance, created, **kwargs):
    if sender not in _TRACKED_MODELS:
        return

    entity_type = _TRACKED_MODELS[sender]

    if created:
        action_type = AuditActionType.CREATE
        description = f"Створено об'єкт {sender.__name__} з id={instance.pk}."
    else:
        action_type = AuditActionType.UPDATE
        description = f"Оновлено об'єкт {sender.__name__} з id={instance.pk}."

    acting_user = getattr(instance, "created_by", None)

    AuditLog.objects.create(
        user=acting_user if acting_user else None,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=instance.pk,
        description=description,
    )


@receiver(post_delete)
def log_model_delete(sender, instance, **kwargs):
    if sender not in _TRACKED_MODELS:
        return

    entity_type = _TRACKED_MODELS[sender]
    acting_user = getattr(instance, "created_by", None)

    AuditLog.objects.create(
        user=acting_user if acting_user else None,
        action_type=AuditActionType.DELETE,
        entity_type=entity_type,
        entity_id=instance.pk,
        description=f"Видалено об'єкт {sender.__name__} з id={instance.pk}.",
    )