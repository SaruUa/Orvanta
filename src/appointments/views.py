from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from config.csv_export import (
    build_csv_response,
    format_csv_date,
    format_csv_datetime,
    format_csv_time,
)
from config.utils import filtered_paginated_response
from users.decorators import employee_manager_admin_required, manager_or_admin_required
from users.models import UserRole

from .forms import AppointmentActualPriceForm, AppointmentFilterForm, AppointmentForm
from .models import Appointment, AppointmentStatus, AppointmentStatusHistory

APPOINTMENTS_PAGE_SIZE = 10


def _organization_appointments_queryset(user):
    if user.organization_id is None:
        return Appointment.objects.none()
    return Appointment.objects.select_related(
        'client',
        'service',
        'employee',
    ).filter(organization=user.organization)


def _filtered_appointments_queryset(user, data):
    appointments = _organization_appointments_queryset(user)

    if user.role == UserRole.EMPLOYEE:
        appointments = appointments.filter(employee=user)

    filter_form = AppointmentFilterForm(
        data or None,
        organization=user.organization,
    )

    if filter_form.is_valid():
        appointment_date = filter_form.cleaned_data.get('appointment_date')
        status = filter_form.cleaned_data.get('status')
        employee = filter_form.cleaned_data.get('employee')

        if appointment_date:
            appointments = appointments.filter(appointment_date=appointment_date)

        if status:
            appointments = appointments.filter(status=status)

        if employee:
            appointments = appointments.filter(employee=employee)

    return appointments, filter_form


def _employee_display(employee):
    return employee.get_full_name() or employee.username


def _redirect_back_to_appointments(request):
    next_url = request.POST.get('next')

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)

    return redirect('appointment_list')


@employee_manager_admin_required
def appointment_list_view(request):
    appointments, filter_form = _filtered_appointments_queryset(request.user, request.GET)
    return filtered_paginated_response(
        request, appointments, APPOINTMENTS_PAGE_SIZE,
        'appointments/appointment_list.html',
        extra_context={'filter_form': filter_form},
    )


@employee_manager_admin_required
def appointment_export_csv_view(request):
    appointments, _filter_form = _filtered_appointments_queryset(request.user, request.GET)
    filename = f'appointments_export_{timezone.localdate():%Y%m%d}.csv'
    headers = [
        'ID',
        'Клієнт',
        'Послуга',
        'Базова вартість послуги',
        'Фактична вартість запису',
        'Співробітник',
        'Дата',
        'Час початку',
        'Час завершення',
        'Статус',
        'Коментар',
        'Дата створення',
        'Дата оновлення',
    ]
    rows = (
        [
            appointment.pk,
            appointment.client.full_name,
            appointment.service.name,
            appointment.service.price,
            appointment.actual_price if appointment.actual_price is not None else '',
            _employee_display(appointment.employee),
            format_csv_date(appointment.appointment_date),
            format_csv_time(appointment.start_time),
            format_csv_time(appointment.end_time),
            appointment.get_status_display(),
            appointment.comment,
            format_csv_datetime(appointment.created_at),
            format_csv_datetime(appointment.updated_at),
        ]
        for appointment in appointments
    )

    return build_csv_response(filename, headers, rows)


@manager_or_admin_required
@require_POST
def appointment_actual_price_update_view(request, pk):
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        organization=request.user.organization,
    )
    form = AppointmentActualPriceForm(request.POST, instance=appointment)

    if form.is_valid():
        appointment = form.save(commit=False)
        appointment.save(update_fields=['actual_price', 'updated_at'])
        messages.success(request, 'Фактичну вартість запису оновлено.')
    else:
        messages.error(request, 'Перевірте фактичну вартість запису.')

    return _redirect_back_to_appointments(request)


@manager_or_admin_required
def appointment_create_view(request):
    if request.method == 'POST':
        form = AppointmentForm(
            request.POST,
            organization=request.user.organization,
        )
        if form.is_valid():
            if request.user.organization is None:
                messages.error(request, 'Ваш користувач не прив’язаний до організації.')
                return redirect('appointment_list')

            appointment = form.save(commit=False)
            appointment.created_by = request.user
            appointment.organization = request.user.organization
            appointment.save()

            AppointmentStatusHistory.objects.create(
                appointment=appointment,
                old_status=appointment.status,
                new_status=appointment.status,
                changed_by=request.user,
                comment='Початковий статус запису.',
                organization=appointment.organization,
            )

            messages.success(request, 'Запис успішно створено.')
            return redirect('appointment_list')
    else:
        form = AppointmentForm(organization=request.user.organization)

    return render(
        request,
        'appointments/appointment_form.html',
        {
            'form': form,
            'title': 'Створення запису',
        },
    )


@manager_or_admin_required
def appointment_update_view(request, pk):
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        organization=request.user.organization,
    )
    old_status = appointment.status

    if request.method == 'POST':
        form = AppointmentForm(
            request.POST,
            instance=appointment,
            organization=request.user.organization,
        )
        if form.is_valid():
            updated_appointment = form.save(commit=False)
            updated_appointment.organization = request.user.organization
            updated_appointment.save()

            if old_status != updated_appointment.status:
                AppointmentStatusHistory.objects.create(
                    appointment=updated_appointment,
                    old_status=old_status,
                    new_status=updated_appointment.status,
                    changed_by=request.user,
                    comment='Статус змінено через форму редагування запису.',
                    organization=updated_appointment.organization,
                )

            messages.success(request, 'Запис успішно оновлено.')
            return redirect('appointment_list')
    else:
        form = AppointmentForm(
            instance=appointment,
            organization=request.user.organization,
        )

    return render(
        request,
        'appointments/appointment_form.html',
        {
            'form': form,
            'title': 'Редагування запису',
        },
    )


@employee_manager_admin_required
def appointment_detail_view(request, pk):
    appointment = get_object_or_404(
        _organization_appointments_queryset(request.user),
        pk=pk,
    )

    if request.user.role == UserRole.EMPLOYEE and appointment.employee != request.user:
        messages.error(request, 'У вас немає прав доступу до цього запису.')
        return redirect('appointment_list')

    status_history = appointment.status_history.select_related('changed_by').filter(
        organization=request.user.organization,
    )

    return render(
        request,
        'appointments/appointment_detail.html',
        {
            'appointment': appointment,
            'status_history': status_history,
        },
    )


@employee_manager_admin_required
@require_POST
def appointment_quick_status_update_view(request, pk, new_status):
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        organization=request.user.organization,
    )

    if request.user.role == UserRole.EMPLOYEE and appointment.employee != request.user:
        messages.error(request, 'У вас немає прав для зміни цього запису.')
        return redirect('appointment_list')

    allowed_statuses = {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.COMPLETED,
    }

    if new_status not in allowed_statuses:
        messages.error(request, 'Невірна дія для зміни статусу.')
        return redirect('appointment_list')

    if appointment.status == new_status:
        messages.error(request, 'Запис уже має цей статус.')
        return redirect('appointment_list')

    old_status = appointment.status
    appointment.status = new_status
    appointment.save(update_fields=['status', 'updated_at'])

    AppointmentStatusHistory.objects.create(
        appointment=appointment,
        old_status=old_status,
        new_status=new_status,
        changed_by=request.user,
        comment='Статус змінено швидкою дією зі списку записів.',
        organization=appointment.organization,
    )

    messages.success(request, 'Статус запису успішно оновлено.')
    return redirect('appointment_list')
