from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from users.decorators import employee_manager_admin_required, manager_or_admin_required

from .forms import AppointmentFilterForm, AppointmentForm
from .models import Appointment, AppointmentStatus, AppointmentStatusHistory


@employee_manager_admin_required
def appointment_list_view(request):
    appointments = Appointment.objects.select_related(
        'client',
        'service',
        'employee',
    ).all()

    if request.user.role == 'employee':
        appointments = appointments.filter(employee=request.user)

    filter_form = AppointmentFilterForm(request.GET or None)

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

    return render(
        request,
        'appointments/appointment_list.html',
        {
            'appointments': appointments,
            'filter_form': filter_form,
        },
    )


@manager_or_admin_required
def appointment_create_view(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.created_by = request.user
            appointment.save()

            AppointmentStatusHistory.objects.create(
                appointment=appointment,
                old_status=appointment.status,
                new_status=appointment.status,
                changed_by=request.user,
                comment='Початковий статус запису.',
            )

            messages.success(request, 'Запис успішно створено.')
            return redirect('appointment_list')
    else:
        form = AppointmentForm()

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
    appointment = get_object_or_404(Appointment, pk=pk)
    old_status = appointment.status

    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            updated_appointment = form.save()

            if old_status != updated_appointment.status:
                AppointmentStatusHistory.objects.create(
                    appointment=updated_appointment,
                    old_status=old_status,
                    new_status=updated_appointment.status,
                    changed_by=request.user,
                    comment='Статус змінено через форму редагування запису.',
                )

            messages.success(request, 'Запис успішно оновлено.')
            return redirect('appointment_list')
    else:
        form = AppointmentForm(instance=appointment)

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
        Appointment.objects.select_related('client', 'service', 'employee'),
        pk=pk,
    )

    if request.user.role == 'employee' and appointment.employee != request.user:
        messages.error(request, 'У вас немає прав доступу до цього запису.')
        return redirect('appointment_list')

    status_history = appointment.status_history.select_related('changed_by').all()

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
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.user.role == 'employee' and appointment.employee != request.user:
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
    )

    messages.success(request, 'Статус запису успішно оновлено.')
    return redirect('appointment_list')
