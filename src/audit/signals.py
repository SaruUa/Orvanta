from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import AuditActionType, AuditEntityType, AuditLog

# Заповнюється у AuditConfig.ready() після того, як усі додатки готові.
_TRACKED_MODELS: dict = {}


def get_instance_organization(instance):
    organization = getattr(instance, 'organization', None)
    return organization if organization else None


def get_user_organization(user):
    if user is None:
        return None
    organization = getattr(user, 'organization', None)
    return organization if organization else None


def get_client_ip(request):
    if request is None:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        organization=get_user_organization(user),
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
        organization=get_user_organization(user),
        action_type=AuditActionType.LOGOUT,
        entity_type=AuditEntityType.AUTH,
        entity_id=user.id,
        description=f"Користувач {user.username} вийшов із системи.",
        ip_address=get_client_ip(request),
    )


# TODO: field-level diff — не реалізовано
# @receiver(pre_save)
# def cache_old_instance_state(sender, instance, **kwargs): ...


def log_model_save(sender, instance, created, **kwargs):
    entity_type = _TRACKED_MODELS[sender]
    if created:
        action_type = AuditActionType.CREATE
        description = f"Створено об'єкт {instance._meta.verbose_name} з id={instance.pk}."
    else:
        action_type = AuditActionType.UPDATE
        description = f"Оновлено об'єкт {instance._meta.verbose_name} з id={instance.pk}."

    # LIMITATION: acting_user = creator, не поточний користувач.
    # Для точної атрибуції потрібен middleware з threading.local.
    acting_user = getattr(instance, "created_by", None)
    organization = get_instance_organization(instance) or get_user_organization(acting_user)

    AuditLog.objects.create(
        user=acting_user if acting_user else None,
        organization=organization,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=instance.pk,
        description=description,
    )


def log_model_delete(sender, instance, **kwargs):
    entity_type = _TRACKED_MODELS[sender]

    # LIMITATION: acting_user = creator, не поточний користувач.
    # Для точної атрибуції потрібен middleware з threading.local.
    acting_user = getattr(instance, "created_by", None)
    organization = get_instance_organization(instance) or get_user_organization(acting_user)

    AuditLog.objects.create(
        user=acting_user if acting_user else None,
        organization=organization,
        action_type=AuditActionType.DELETE,
        entity_type=entity_type,
        entity_id=instance.pk,
        description=f"Видалено об'єкт {instance._meta.verbose_name} з id={instance.pk}.",
    )
