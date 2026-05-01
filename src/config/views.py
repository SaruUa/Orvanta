from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus, AppointmentStatusHistory
from audit.models import AuditLog
from clients.models import Client
from services_catalog.models import Service, ServiceCategory
from users.decorators import admin_required
from users.models import User, UserRole


def get_onboarding_status(user):
    organization = getattr(user, 'organization', None)

    if user.role != UserRole.ADMIN or organization is None:
        return None

    has_service_category = ServiceCategory.objects.filter(
        organization=organization,
    ).exists()
    has_service = Service.objects.filter(
        organization=organization,
        is_active=True,
    ).exists()
    has_employee = User.objects.filter(
        organization=organization,
        role=UserRole.EMPLOYEE,
        is_active=True,
    ).exists()
    has_client = Client.objects.filter(
        organization=organization,
        is_active=True,
    ).exists()
    has_appointment = Appointment.objects.filter(
        organization=organization,
    ).exists()

    steps = [
        {
            'key': 'service_category',
            'label': 'Створіть першу категорію послуг',
            'is_done': has_service_category,
            'url': reverse('category_create'),
            'action_label': 'Створити категорію',
        },
        {
            'key': 'service',
            'label': 'Створіть першу послугу',
            'is_done': has_service,
            'url': reverse('service_create'),
            'action_label': 'Створити послугу',
        },
        {
            'key': 'employee',
            'label': 'Додайте співробітника',
            'is_done': has_employee,
            'url': reverse('user_create'),
            'action_label': 'Додати співробітника',
        },
        {
            'key': 'client',
            'label': 'Додайте клієнта',
            'is_done': has_client,
            'url': reverse('client_create'),
            'action_label': 'Додати клієнта',
        },
        {
            'key': 'appointment',
            'label': 'Створіть перший запис',
            'is_done': has_appointment,
            'url': reverse('appointment_create'),
            'action_label': 'Створити запис',
        },
    ]

    return {
        'steps': steps,
        'is_complete': all(step['is_done'] for step in steps),
    }


def get_dashboard_analytics(user):
    user_organization = user.organization

    appointments = Appointment.objects.select_related(
        'client',
        'service',
        'employee',
    ).filter(organization=user_organization)

    if user.role == UserRole.EMPLOYEE:
        appointments = appointments.filter(employee=user)

    raw_status_counts = (
        appointments.values('status')
        .annotate(total=Count('id'))
        .order_by('status')
    )

    status_map = dict(Appointment._meta.get_field('status').choices)
    status_class_map = {
        AppointmentStatus.PLANNED: 'planned',
        AppointmentStatus.CONFIRMED: 'confirmed',
        AppointmentStatus.COMPLETED: 'completed',
        AppointmentStatus.CANCELLED: 'cancelled',
    }
    appointments_total = appointments.count()
    status_counts = [
        {
            'key': item['status'],
            'status': status_map.get(item['status'], item['status']),
            'total': item['total'],
            'percentage': round((item['total'] / appointments_total) * 100) if appointments_total else 0,
            'css_class': status_class_map.get(item['status'], 'default'),
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
    planned_count = appointments.filter(status=AppointmentStatus.PLANNED).count()
    confirmed_count = appointments.filter(status=AppointmentStatus.CONFIRMED).count()
    completed_without_price_count = appointments.filter(
        status=AppointmentStatus.COMPLETED,
        actual_price__isnull=True,
    ).count()
    revenue_appointments = appointments.filter(
        status=AppointmentStatus.COMPLETED,
        actual_price__isnull=False,
    )
    revenue_totals = revenue_appointments.aggregate(
        total_revenue=Sum('actual_price'),
        average_check=Avg('actual_price'),
    )
    total_revenue = (revenue_totals['total_revenue'] or Decimal('0.00')).quantize(
        Decimal('0.01'),
    )
    average_check = (revenue_totals['average_check'] or Decimal('0.00')).quantize(
        Decimal('0.01'),
    )

    clients = Client.objects.filter(organization=user_organization)
    services = Service.objects.filter(organization=user_organization)

    return {
        'appointments_queryset': appointments,
        'clients_count': clients.count(),
        'active_clients_count': clients.filter(is_active=True).count(),
        'services_count': services.count(),
        'active_services_count': services.filter(is_active=True).count(),
        'appointments_count': appointments.count(),
        'employees_count': User.objects.filter(
            role=UserRole.EMPLOYEE,
            organization=user_organization,
        ).count(),
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'planned_count': planned_count,
        'confirmed_count': confirmed_count,
        'completed_without_price_count': completed_without_price_count,
        'total_revenue': total_revenue,
        'average_check': average_check,
        'revenue_appointments_count': revenue_appointments.count(),
        'status_counts': status_counts,
        'popular_services': popular_services,
        'employee_workload': employee_workload,
    }


@login_required
def home_view(request):
    analytics = get_dashboard_analytics(request.user)
    appointments = analytics.pop('appointments_queryset')
    onboarding = get_onboarding_status(request.user)

    nearest_appointments = (
        appointments.exclude(status=AppointmentStatus.CANCELLED)
        .filter(appointment_date__gte=timezone.localdate())
        .order_by('appointment_date', 'start_time')[:5]
    )

    recent_status_changes = AppointmentStatusHistory.objects.select_related(
        'appointment',
        'appointment__client',
        'appointment__service',
        'changed_by',
    ).filter(organization=request.user.organization).order_by('-changed_at')[:5]

    can_manage_data = (
        request.user.organization_id is not None
        and request.user.role in {UserRole.ADMIN, UserRole.MANAGER}
    )
    can_manage_users = (
        request.user.organization_id is not None
        and request.user.role == UserRole.ADMIN
    )
    quick_actions = []

    if can_manage_data:
        quick_actions.extend([
            {
                'label': 'Створити запис',
                'url': reverse('appointment_create'),
                'style': 'primary',
            },
            {
                'label': 'Додати клієнта',
                'url': reverse('client_create'),
                'style': 'outline-primary',
            },
            {
                'label': 'Додати послугу',
                'url': reverse('service_create'),
                'style': 'outline-secondary',
            },
        ])

    if can_manage_users:
        quick_actions.append({
            'label': 'Додати співробітника',
            'url': reverse('user_create'),
            'style': 'outline-secondary',
        })

    context = {
        **analytics,
        'onboarding': onboarding,
        'nearest_appointments': nearest_appointments,
        'recent_status_changes': recent_status_changes,
        'quick_actions': quick_actions,
        'header_quick_actions': quick_actions[:2],
    }
    return render(request, 'home.html', context)


@admin_required
def admin_dashboard_view(request):
    org_users = User.objects.filter(organization=request.user.organization)

    role_counts = (
        org_users.values('role')
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
        'users_count': org_users.count(),
        'clients_count': Client.objects.filter(organization=request.user.organization).count(),
        'services_count': Service.objects.filter(organization=request.user.organization).count(),
        'appointments_count': Appointment.objects.filter(
            organization=request.user.organization,
        ).count(),
        'role_stats': role_stats,
        'recent_users': org_users.order_by('-date_joined')[:5],
        'recent_logs': AuditLog.objects.select_related('user').filter(
            organization=request.user.organization,
        ).order_by('-created_at')[:10],
    }
    return render(request, 'admin_dashboard.html', context)
