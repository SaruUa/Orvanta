from datetime import date, time
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment, AppointmentStatus
from clients.models import Client
from services_catalog.models import Service, ServiceCategory
from users.models import Organization, User, UserRole

from .views import get_dashboard_analytics, get_onboarding_status


class OnboardingStatusTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Onboarding Org',
            slug='onboarding-org',
        )
        self.other_organization = Organization.objects.create(
            name='Other Onboarding Org',
            slug='other-onboarding-org',
        )
        self.admin = User.objects.create_user(
            username='onboarding_admin',
            email='onboarding_admin@example.com',
            password='StrongPass123!',
            role=UserRole.ADMIN,
            organization=self.organization,
        )

    def _step_map(self, user=None):
        status = get_onboarding_status(user or self.admin)
        return {step['key']: step['is_done'] for step in status['steps']}

    def _create_complete_workspace(self, organization, *, username_prefix='workspace'):
        employee = User.objects.create_user(
            username=f'{username_prefix}_employee',
            email=f'{username_prefix}_employee@example.com',
            password='StrongPass123!',
            role=UserRole.EMPLOYEE,
            organization=organization,
            is_active=True,
        )
        client = Client.objects.create(
            full_name=f'{username_prefix.title()} Client',
            phone=f'+3805009{employee.pk:05d}',
            is_active=True,
            organization=organization,
            created_by=self.admin if organization == self.organization else employee,
        )
        category = ServiceCategory.objects.create(
            name=f'{username_prefix.title()} Category',
            organization=organization,
        )
        service = Service.objects.create(
            category=category,
            name=f'{username_prefix.title()} Service',
            price='100.00',
            duration_minutes=60,
            is_active=True,
            organization=organization,
        )
        Appointment.objects.create(
            client=client,
            service=service,
            employee=employee,
            created_by=self.admin if organization == self.organization else employee,
            appointment_date=date(2026, 5, 10),
            start_time=time(10, 0),
            end_time=time(11, 0),
            organization=organization,
        )

    def test_new_admin_with_empty_organization_sees_onboarding_block(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Початкове налаштування організації')
        self.assertContains(response, reverse('category_create'))
        self.assertFalse(response.context['onboarding']['is_complete'])

    def test_manager_and_employee_do_not_see_onboarding_block(self):
        for role in (UserRole.MANAGER, UserRole.EMPLOYEE):
            user = User.objects.create_user(
                username=f'onboarding_{role}',
                email=f'onboarding_{role}@example.com',
                password='StrongPass123!',
                role=role,
                organization=self.organization,
            )
            self.client.force_login(user)

            response = self.client.get(reverse('home'))

            self.assertEqual(response.status_code, 200)
            self.assertIsNone(response.context['onboarding'])
            self.assertNotContains(response, 'Початкове налаштування організації')

    def test_complete_workspace_hides_onboarding_block(self):
        self._create_complete_workspace(self.organization)
        self.client.force_login(self.admin)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['onboarding']['is_complete'])
        self.assertNotContains(response, 'Початкове налаштування організації')

    def test_onboarding_uses_only_current_organization_data(self):
        self._create_complete_workspace(
            self.other_organization,
            username_prefix='foreign_workspace',
        )

        steps = self._step_map()

        self.assertEqual(
            steps,
            {
                'service_category': False,
                'service': False,
                'employee': False,
                'client': False,
                'appointment': False,
            },
        )

    def test_steps_become_done_after_related_objects_exist(self):
        inactive_employee = User.objects.create_user(
            username='inactive_onboarding_employee',
            email='inactive_onboarding_employee@example.com',
            password='StrongPass123!',
            role=UserRole.EMPLOYEE,
            organization=self.organization,
            is_active=False,
        )
        inactive_client = Client.objects.create(
            full_name='Inactive Onboarding Client',
            phone='+380500910000',
            is_active=False,
            organization=self.organization,
            created_by=self.admin,
        )
        category = ServiceCategory.objects.create(
            name='Onboarding Category',
            organization=self.organization,
        )
        inactive_service = Service.objects.create(
            category=category,
            name='Inactive Onboarding Service',
            price='100.00',
            duration_minutes=60,
            is_active=False,
            organization=self.organization,
        )

        steps = self._step_map()

        self.assertTrue(steps['service_category'])
        self.assertFalse(steps['employee'])
        self.assertFalse(steps['client'])
        self.assertFalse(steps['service'])

        inactive_employee.is_active = True
        inactive_employee.save(update_fields=['is_active'])
        inactive_client.is_active = True
        inactive_client.save(update_fields=['is_active'])
        inactive_service.is_active = True
        inactive_service.save(update_fields=['is_active'])
        Appointment.objects.create(
            client=inactive_client,
            service=inactive_service,
            employee=inactive_employee,
            created_by=self.admin,
            appointment_date=date(2026, 5, 11),
            start_time=time(12, 0),
            end_time=time(13, 0),
            organization=self.organization,
        )

        self.assertEqual(
            self._step_map(),
            {
                'service_category': True,
                'service': True,
                'employee': True,
                'client': True,
                'appointment': True,
            },
        )

    def test_home_does_not_crash_for_admin_without_organization(self):
        admin_without_organization = User.objects.create_user(
            username='admin_without_org',
            email='admin_without_org@example.com',
            password='StrongPass123!',
            role=UserRole.ADMIN,
            organization=None,
        )
        self.client.force_login(admin_without_organization)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['onboarding'])
        self.assertNotContains(response, 'Початкове налаштування організації')


class DashboardRevenueAnalyticsTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Revenue Org',
            slug='revenue-org',
        )
        self.other_organization = Organization.objects.create(
            name='Other Revenue Org',
            slug='other-revenue-org',
        )
        self.admin = User.objects.create_user(
            username='revenue_admin',
            email='revenue_admin@example.com',
            password='StrongPass123!',
            role=UserRole.ADMIN,
            organization=self.organization,
        )
        self.employee = User.objects.create_user(
            username='revenue_employee',
            email='revenue_employee@example.com',
            password='StrongPass123!',
            role=UserRole.EMPLOYEE,
            organization=self.organization,
        )
        self.other_employee = User.objects.create_user(
            username='other_revenue_employee',
            email='other_revenue_employee@example.com',
            password='StrongPass123!',
            role=UserRole.EMPLOYEE,
            organization=self.other_organization,
        )
        self.client_record = Client.objects.create(
            full_name='Revenue Client',
            phone='+380501230001',
            organization=self.organization,
            created_by=self.admin,
        )
        self.other_client_record = Client.objects.create(
            full_name='Other Revenue Client',
            phone='+380501230002',
            organization=self.other_organization,
            created_by=self.other_employee,
        )
        self.category = ServiceCategory.objects.create(
            name='Revenue Category',
            organization=self.organization,
        )
        self.other_category = ServiceCategory.objects.create(
            name='Other Revenue Category',
            organization=self.other_organization,
        )
        self.service = Service.objects.create(
            category=self.category,
            name='Revenue Service',
            price='100.00',
            duration_minutes=60,
            organization=self.organization,
        )
        self.other_service = Service.objects.create(
            category=self.other_category,
            name='Other Revenue Service',
            price='100.00',
            duration_minutes=60,
            organization=self.other_organization,
        )

    def _create_appointment(
        self,
        *,
        organization=None,
        employee=None,
        status=AppointmentStatus.COMPLETED,
        actual_price=None,
        day=1,
    ):
        organization = organization or self.organization
        client = self.client_record
        service = self.service
        created_by = self.admin

        if organization != self.organization:
            client = self.other_client_record
            service = self.other_service
            created_by = self.other_employee
            employee = employee or self.other_employee
        else:
            employee = employee or self.employee

        return Appointment.objects.create(
            client=client,
            service=service,
            employee=employee,
            created_by=created_by,
            appointment_date=date(2026, 6, day),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status=status,
            actual_price=actual_price,
            organization=organization,
        )

    def test_dashboard_revenue_counts_completed_paid_appointments_only(self):
        self._create_appointment(actual_price='100.00', day=1)
        self._create_appointment(actual_price='250.00', day=2)
        self._create_appointment(actual_price=None, day=3)
        self._create_appointment(
            status=AppointmentStatus.CANCELLED,
            actual_price='900.00',
            day=4,
        )
        self._create_appointment(
            status=AppointmentStatus.PLANNED,
            actual_price='800.00',
            day=5,
        )
        self._create_appointment(
            status=AppointmentStatus.CONFIRMED,
            actual_price='700.00',
            day=6,
        )
        self._create_appointment(
            organization=self.other_organization,
            employee=self.other_employee,
            actual_price='1000.00',
            day=7,
        )

        analytics = get_dashboard_analytics(self.admin)

        self.assertEqual(analytics['total_revenue'], Decimal('350.00'))
        self.assertEqual(analytics['average_check'], Decimal('175.00'))
        self.assertEqual(analytics['revenue_appointments_count'], 2)
        self.assertEqual(analytics['planned_count'], 1)
        self.assertEqual(analytics['confirmed_count'], 1)
        self.assertEqual(analytics['completed_without_price_count'], 1)

    def test_dashboard_revenue_defaults_to_zero_without_completed_paid_appointments(self):
        self._create_appointment(status=AppointmentStatus.COMPLETED, actual_price=None)
        self._create_appointment(status=AppointmentStatus.CANCELLED, actual_price='100.00')

        analytics = get_dashboard_analytics(self.admin)

        self.assertEqual(analytics['total_revenue'], Decimal('0.00'))
        self.assertEqual(analytics['average_check'], Decimal('0.00'))
        self.assertEqual(analytics['revenue_appointments_count'], 0)
