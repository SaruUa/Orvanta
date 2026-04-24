from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AppointmentForm
from .models import Appointment


@login_required
def appointment_list_view(request):
    appointments = Appointment.objects.select_related(
        'client',
        'service',
        'employee',
    ).all()
    return render(
        request,
        'appointments/appointment_list.html',
        {'appointments': appointments},
    )


@login_required
def appointment_create_view(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.created_by = request.user
            appointment.save()
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


@login_required
def appointment_update_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
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


@login_required
def appointment_detail_view(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related('client', 'service', 'employee'),
        pk=pk,
    )
    return render(
        request,
        'appointments/appointment_detail.html',
        {'appointment': appointment},
    )
