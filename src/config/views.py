from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from appointments.models import Appointment, AppointmentStatus, AppointmentStatusHistory
from audit.models import AuditLog
from clients.models import Client
from services_catalog.models import Service
from users.decorators import admin_required
from users.models import User, UserRole


def get_dashboard_analytics(user):
    appointments = Appointment.objects.select_related(
        'client',
        'service',
        'employee',
    )

    if user.role == UserRole.EMPLOYEE:
        appointments = appointments.filter(employee=user)

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

    popular_services = list(
        appointments.values('service__name')
        .annotate(total=Count('id'))
        .order_by('-total', 'service__name')[:5]
    )

    employee_workload = list(
        appointments.values('employee__username')
        .annotate(total=Count('id'))
        .order_by('-total', 'employee__username')[:5]
    )

    completed_count = appointments.filter(status=AppointmentStatus.COMPLETED).count()
    cancelled_count = appointments.filter(status=AppointmentStatus.CANCELLED).count()

    return {
        'appointments_queryset': appointments,
        'clients_count': Client.objects.count(),
        'active_clients_count': Client.objects.filter(is_active=True).count(),
        'services_count': Service.objects.count(),
        'active_services_count': Service.objects.filter(is_active=True).count(),
        'appointments_count': appointments.count(),
        'employees_count': User.objects.filter(role=UserRole.EMPLOYEE).count(),
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'status_counts': status_counts,
        'popular_services': popular_services,
        'employee_workload': employee_workload,
    }


@login_required
def home_view(request):
    analytics = get_dashboard_analytics(request.user)
    appointments = analytics.pop('appointments_queryset')

    nearest_appointments = appointments.order_by('appointment_date', 'start_time')[:5]

    recent_status_changes = AppointmentStatusHistory.objects.select_related(
        'appointment',
        'changed_by',
    ).order_by('-changed_at')[:5]

    context = {
        **analytics,
        'nearest_appointments': nearest_appointments,
        'recent_status_changes': recent_status_changes,
    }
    return render(request, 'home.html', context)


@admin_required
def admin_dashboard_view(request):
    role_counts = (
        User.objects.values('role')
        .annotate(total=Count('id'))
        .order_by('role')
    )

    role_map = dict(User._meta.get_field('role').choices)
    role_stats = [
        {
            'role': role_map.get(item['role'], item['role']),
            'total': item['total'],
        }
        for item in role_counts
    ]

    context = {
        'users_count': User.objects.count(),
        'clients_count': Client.objects.count(),
        'services_count': Service.objects.count(),
        'appointments_count': Appointment.objects.count(),
        'role_stats': role_stats,
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_logs': AuditLog.objects.select_related('user').order_by('-created_at')[:10],
    }
    return render(request, 'admin_dashboard.html', context)
