from datetime import date, time
from decimal import Decimal

from django.test import TestCase

from clients.models import Client
from services_catalog.models import Service, ServiceCategory
from users.models import Organization, User, UserRole

from .models import Appointment, AppointmentStatus, AppointmentStatusHistory


class AppointmentModelSetup(TestCase):
    """Базовий клас з готовими об'єктами для тестів записів."""

    def setUp(self):
        self.org = Organization.objects.create(name='Appt Org', slug='appt-org')
        self.admin = User.objects.create_user(
            username='appt_admin', password='pass',
            organization=self.org, role=UserRole.ADMIN,
        )
        self.employee = User.objects.create_user(
            username='appt_emp', password='pass',
            organization=self.org, role=UserRole.EMPLOYEE,
        )
        self.client_obj = Client.objects.create(
            full_name='Тест Клієнт',
            phone='+380501234567',
            organization=self.org,
            created_by=self.admin,
        )
        self.category = ServiceCategory.objects.create(name='Категорія', organization=self.org)
        self.service = Service.objects.create(
            name='Тест Послуга',
            price=Decimal('500'),
            duration_minutes=60,
            category=self.category,
            organization=self.org,
        )

    def _make_appointment(self, **kwargs):
        defaults = dict(
            client=self.client_obj,
            service=self.service,
            employee=self.employee,
            created_by=self.admin,
            appointment_date=date(2025, 6, 15),
            start_time=time(10, 0),
            end_time=time(11, 0),
            organization=self.org,
        )
        defaults.update(kwargs)
        return Appointment.objects.create(**defaults)


class AppointmentModelTests(AppointmentModelSetup):
    def test_str_shows_client_service_and_date(self):
        appt = self._make_appointment()
        self.assertIn('Тест Клієнт', str(appt))
        self.assertIn('Тест Послуга', str(appt))
        self.assertIn('2025-06-15', str(appt))

    def test_default_status_is_planned(self):
        appt = self._make_appointment()
        self.assertEqual(appt.status, AppointmentStatus.PLANNED)

    def test_actual_price_nullable(self):
        appt = self._make_appointment()
        self.assertIsNone(appt.actual_price)

    def test_actual_price_can_be_set(self):
        appt = self._make_appointment(actual_price=Decimal('450'))
        self.assertEqual(appt.actual_price, Decimal('450'))

    def test_status_choices_exist(self):
        statuses = [c[0] for c in AppointmentStatus.choices]
        self.assertIn('planned', statuses)
        self.assertIn('confirmed', statuses)
        self.assertIn('completed', statuses)
        self.assertIn('cancelled', statuses)

    def test_appointment_linked_to_organization(self):
        appt = self._make_appointment()
        self.assertEqual(appt.organization, self.org)


class AppointmentStatusHistoryModelTests(AppointmentModelSetup):
    def test_str_shows_status_transition(self):
        appt = self._make_appointment()
        history = AppointmentStatusHistory.objects.create(
            appointment=appt,
            old_status=AppointmentStatus.PLANNED,
            new_status=AppointmentStatus.COMPLETED,
            changed_by=self.admin,
            organization=self.org,
        )
        result = str(history)
        self.assertIn('planned', result)
        self.assertIn('completed', result)

    def test_history_linked_to_appointment(self):
        appt = self._make_appointment()
        history = AppointmentStatusHistory.objects.create(
            appointment=appt,
            old_status=AppointmentStatus.PLANNED,
            new_status=AppointmentStatus.CONFIRMED,
            changed_by=self.admin,
            organization=self.org,
        )
        self.assertEqual(history.appointment, appt)
        self.assertIn(history, appt.status_history.all())

    def test_multiple_history_entries_ordered_newest_first(self):
        appt = self._make_appointment()
        h1 = AppointmentStatusHistory.objects.create(
            appointment=appt,
            old_status=AppointmentStatus.PLANNED,
            new_status=AppointmentStatus.CONFIRMED,
            changed_by=self.admin,
            organization=self.org,
        )
        h2 = AppointmentStatusHistory.objects.create(
            appointment=appt,
            old_status=AppointmentStatus.CONFIRMED,
            new_status=AppointmentStatus.COMPLETED,
            changed_by=self.admin,
            organization=self.org,
        )
        history = list(appt.status_history.all())
        self.assertEqual(history[0], h2)  # найновіший перший
        self.assertEqual(history[1], h1)
