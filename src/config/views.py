from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from appointments.models import Appointment, AppointmentStatusHistory
from clients.models import Client
from services_catalog.models import Service
from users.models import User, UserRole


@login_required
def home_view(request):
    appointments = Appointment.objects.select_related(
        'client',
        'service',
        'employee',
    )

    if request.user.role == UserRole.EMPLOYEE:
        appointments = appointments.filter(employee=request.user)

    raw_status_counts = (
        appointments.values('status')
        .annotate(total=Count('id'))
        .order_by('status')
    )

    status_map = dict(Appointment._meta.get_field('status').choices)
    status_counts = [
        {
            'status': status_map.get(item['status'], item['status']),
            'total': item['total'],
        }
        for item in raw_status_counts
    ]

    nearest_appointments = appointments.order_by('appointment_date', 'start_time')[:5]

    recent_status_changes = AppointmentStatusHistory.objects.select_related(
        'appointment',
        'changed_by',
    ).order_by('-changed_at')[:5]

    context = {
        'clients_count': Client.objects.count(),
        'active_clients_count': Client.objects.filter(is_active=True).count(),
        'services_count': Service.objects.count(),
        'active_services_count': Service.objects.filter(is_active=True).count(),
        'appointments_count': appointments.count(),
        'employees_count': User.objects.filter(role=UserRole.EMPLOYEE).count(),
        'status_counts': status_counts,
        'nearest_appointments': nearest_appointments,
        'recent_status_changes': recent_status_changes,
    }
    return render(request, 'home.html', context)
