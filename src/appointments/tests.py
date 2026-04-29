from django.test import TestCase

from clients.models import Client
from services_catalog.models import Service, ServiceCategory
from users.models import Organization, User, UserRole

from .forms import AppointmentForm
from .models import Appointment, AppointmentStatus


class AppointmentFormConflictValidationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Org One', slug='org-one')
        self.other_organization = Organization.objects.create(name='Org Two', slug='org-two')

        self.manager = User.objects.create_user(
            username='manager_user',
            email='manager@example.com',
            password='StrongPass123!',
            role=UserRole.MANAGER,
            organization=self.organization,
        )
        self.employee = User.objects.create_user(
            username='employee_one',
            email='employee_one@example.com',
            password='StrongPass123!',
            role=UserRole.EMPLOYEE,
            organization=self.organization,
            is_active=True,
        )
        self.employee_two = User.objects.create_user(
            username='employee_two',
            email='employee_two@example.com',
            password='StrongPass123!',
            role=UserRole.EMPLOYEE,
            organization=self.organization,
            is_active=True,
        )
        self.other_employee = User.objects.create_user(
            username='employee_other_org',
            email='employee_other@example.com',
            password='StrongPass123!',
            role=UserRole.EMPLOYEE,
            organization=self.other_organization,
            is_active=True,
        )

        self.client = Client.objects.create(
            full_name='Client One',
            phone='+380500000001',
            organization=self.organization,
            created_by=self.manager,
        )
        self.other_client = Client.objects.create(
            full_name='Client Two',
            phone='+380500000002',
            organization=self.other_organization,
            created_by=self.other_employee,
        )

        self.category = ServiceCategory.objects.create(
            name='Category One',
            organization=self.organization,
        )
        self.other_category = ServiceCategory.objects.create(
            name='Category Two',
            organization=self.other_organization,
        )

        self.service = Service.objects.create(
            category=self.category,
            name='Service One',
            price='1000.00',
            duration_minutes=60,
            organization=self.organization,
        )
        self.other_service = Service.objects.create(
            category=self.other_category,
            name='Service Two',
            price='2000.00',
            duration_minutes=60,
            organization=self.other_organization,
        )

    def _create_appointment(
        self,
        *,
        organization,
        client,
        service,
        employee,
        appointment_date='2026-05-10',
        start_time='10:00',
        end_time='11:00',
        status=AppointmentStatus.PLANNED,
    ):
        return Appointment.objects.create(
            client=client,
            service=service,
            employee=employee,
            created_by=self.manager,
            organization=organization,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )

    def _form_data(
        self,
        *,
        client=None,
        service=None,
        employee=None,
        appointment_date='2026-05-10',
        start_time='10:00',
        end_time='11:00',
        status=AppointmentStatus.PLANNED,
    ):
        return {
            'client': (client or self.client).pk,
            'service': (service or self.service).pk,
            'employee': (employee or self.employee).pk,
            'appointment_date': appointment_date,
            'start_time': start_time,
            'end_time': end_time,
            'status': status,
            'comment': '',
        }

    def test_can_create_appointment_when_time_does_not_overlap(self):
        self._create_appointment(
            organization=self.organization,
            client=self.client,
            service=self.service,
            employee=self.employee,
            start_time='10:00',
            end_time='11:00',
        )

        form = AppointmentForm(
            data=self._form_data(start_time='11:00', end_time='12:00'),
            organization=self.organization,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_cannot_create_appointment_when_time_overlaps_for_same_employee(self):
        self._create_appointment(
            organization=self.organization,
            client=self.client,
            service=self.service,
            employee=self.employee,
            start_time='10:00',
            end_time='11:00',
        )

        form = AppointmentForm(
            data=self._form_data(start_time='10:30', end_time='11:30'),
            organization=self.organization,
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            'У цього співробітника вже є запис на обраний проміжок часу.',
            form.non_field_errors(),
        )

    def test_cancelled_appointment_does_not_block_new_one(self):
        self._create_appointment(
            organization=self.organization,
            client=self.client,
            service=self.service,
            employee=self.employee,
            start_time='10:00',
            end_time='11:00',
            status=AppointmentStatus.CANCELLED,
        )

        form = AppointmentForm(
            data=self._form_data(start_time='10:30', end_time='10:45'),
            organization=self.organization,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_can_create_same_time_for_other_employee(self):
        self._create_appointment(
            organization=self.organization,
            client=self.client,
            service=self.service,
            employee=self.employee,
        )

        form = AppointmentForm(
            data=self._form_data(employee=self.employee_two),
            organization=self.organization,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_can_create_same_time_in_other_organization(self):
        self._create_appointment(
            organization=self.organization,
            client=self.client,
            service=self.service,
            employee=self.employee,
        )

        form = AppointmentForm(
            data=self._form_data(
                client=self.other_client,
                service=self.other_service,
                employee=self.other_employee,
            ),
            organization=self.other_organization,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_update_does_not_conflict_with_itself(self):
        appointment = self._create_appointment(
            organization=self.organization,
            client=self.client,
            service=self.service,
            employee=self.employee,
            start_time='09:00',
            end_time='10:00',
        )

        form = AppointmentForm(
            data=self._form_data(start_time='09:00', end_time='10:00'),
            instance=appointment,
            organization=self.organization,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_update_fails_when_time_overlaps_other_appointment(self):
        self._create_appointment(
            organization=self.organization,
            client=self.client,
            service=self.service,
            employee=self.employee,
            start_time='09:00',
            end_time='10:00',
        )
        editable_appointment = self._create_appointment(
            organization=self.organization,
            client=self.client,
            service=self.service,
            employee=self.employee,
            start_time='10:00',
            end_time='11:00',
        )

        form = AppointmentForm(
            data=self._form_data(start_time='09:30', end_time='10:30'),
            instance=editable_appointment,
            organization=self.organization,
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            'У цього співробітника вже є запис на обраний проміжок часу.',
            form.non_field_errors(),
        )

    def test_start_time_must_be_earlier_than_end_time(self):
        form = AppointmentForm(
            data=self._form_data(start_time='12:00', end_time='12:00'),
            organization=self.organization,
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            'Час завершення запису повинен бути пізнішим за час початку.',
            form.non_field_errors(),
        )
