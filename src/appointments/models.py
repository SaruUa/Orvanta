from django.conf import settings
from django.db import models

from clients.models import Client
from services_catalog.models import Service


class AppointmentStatus(models.TextChoices):
    PLANNED = 'planned', 'Заплановано'
    CONFIRMED = 'confirmed', 'Підтверджено'
    COMPLETED = 'completed', 'Виконано'
    CANCELLED = 'cancelled', 'Скасовано'


class Appointment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='appointments')
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='employee_appointments',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_appointments',
    )
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PLANNED,
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment_date', '-start_time']
        verbose_name = 'Запис'
        verbose_name_plural = 'Записи'

    def __str__(self):
        return f'{self.client.full_name} - {self.service.name} ({self.appointment_date})'


class AppointmentStatusHistory(models.Model):
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='status_history',
    )
    old_status = models.CharField(max_length=20, choices=AppointmentStatus.choices)
    new_status = models.CharField(max_length=20, choices=AppointmentStatus.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='changed_appointment_statuses',
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Історія статусу запису'
        verbose_name_plural = 'Історія статусів записів'

    def __str__(self):
        return f'{self.appointment_id}: {self.old_status} -> {self.new_status}'