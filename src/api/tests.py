from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from appointments.models import Appointment, AppointmentStatus
from clients.models import Client
from services_catalog.models import Service, ServiceCategory
from users.models import Organization, UserRole


class ReadOnlyApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.organization = Organization.objects.create(
            name='Org One',
            slug='org-one',
        )
        self.other_organization = Organization.objects.create(
            name='Org Two',
            slug='org-two',
        )

        self.user = user_model.objects.create_user(
            username='api_user',
            password='testpass123',
            role=UserRole.ADMIN,
            organization=self.organization,
        )

        self.employee = user_model.objects.create_user(
            username='employee_1',
            password='testpass123',
            role=UserRole.EMPLOYEE,
            organization=self.organization,
        )
        self.other_employee = user_model.objects.create_user(
            username='employee_2',
            password='testpass123',
            role=UserRole.EMPLOYEE,
            organization=self.other_organization,
        )

        self.client.force_authenticate(user=self.user)

        self.client_entity = Client.objects.create(
            full_name='Іван Петренко',
            phone='+380501112233',
            email='ivan@example.com',
            created_by=self.user,
            organization=self.organization,
        )
        self.other_client = Client.objects.create(
            full_name='Марія Іванова',
            phone='+380501112244',
            email='maria@example.com',
            created_by=self.user,
            organization=self.other_organization,
        )

        self.category = ServiceCategory.objects.create(
            name='Тату',
            organization=self.organization,
        )
        self.other_category = ServiceCategory.objects.create(
            name='Пірсинг',
            organization=self.other_organization,
        )
        self.service = Service.objects.create(
            category=self.category,
            name='Контур',
            description='Контурна робота',
            price='1200.00',
            duration_minutes=90,
            organization=self.organization,
        )
        self.other_service = Service.objects.create(
            category=self.other_category,
            name='Септум',
            description='Пірсинг септуму',
            price='900.00',
            duration_minutes=45,
            organization=self.other_organization,
        )
        self.appointment = Appointment.objects.create(
            client=self.client_entity,
            service=self.service,
            employee=self.employee,
            created_by=self.user,
            organization=self.organization,
            appointment_date=date(2026, 4, 28),
            start_time=time(12, 0),
            end_time=time(13, 30),
            status=AppointmentStatus.CONFIRMED,
            actual_price='1300.00',
        )
        self.other_appointment = Appointment.objects.create(
            client=self.other_client,
            service=self.other_service,
            employee=self.other_employee,
            created_by=self.other_employee,
            organization=self.other_organization,
            appointment_date=date(2026, 4, 29),
            start_time=time(14, 0),
            end_time=time(15, 0),
            status=AppointmentStatus.PLANNED,
        )

    def test_clients_list_and_detail(self):
        list_response = self.client.get('/api/clients/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]['id'], self.client_entity.id)

        detail_response = self.client.get(f'/api/clients/{self.client_entity.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['full_name'], self.client_entity.full_name)

        other_detail_response = self.client.get(f'/api/clients/{self.other_client.id}/')
        self.assertEqual(other_detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_services_list_and_detail(self):
        list_response = self.client.get('/api/services/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]['category_name'], self.category.name)

        detail_response = self.client.get(f'/api/services/{self.service.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['name'], self.service.name)
        self.assertEqual(detail_response.data['category_name'], self.category.name)

        other_detail_response = self.client.get(f'/api/services/{self.other_service.id}/')
        self.assertEqual(other_detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_appointments_list_and_detail(self):
        list_response = self.client.get('/api/appointments/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

        appointment_data = list_response.data[0]
        self.assertEqual(appointment_data['client_full_name'], self.client_entity.full_name)
        self.assertEqual(appointment_data['service_name'], self.service.name)
        self.assertEqual(appointment_data['employee_username'], self.employee.username)
        self.assertEqual(appointment_data['status'], AppointmentStatus.CONFIRMED)
        self.assertEqual(appointment_data['actual_price'], '1300.00')

        detail_response = self.client.get(f'/api/appointments/{self.appointment.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['id'], self.appointment.id)
        self.assertEqual(detail_response.data['client_full_name'], self.client_entity.full_name)
        self.assertEqual(detail_response.data['service_name'], self.service.name)
        self.assertEqual(detail_response.data['employee_username'], self.employee.username)
        self.assertEqual(detail_response.data['appointment_date'], '2026-04-28')
        self.assertEqual(detail_response.data['start_time'], '12:00:00')
        self.assertEqual(detail_response.data['end_time'], '13:30:00')
        self.assertEqual(detail_response.data['actual_price'], '1300.00')

        other_detail_response = self.client.get(f'/api/appointments/{self.other_appointment.id}/')
        self.assertEqual(other_detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_endpoints_are_read_only(self):
        response = self.client.post('/api/clients/', data={'full_name': 'Тест'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_unauthorized_user_cannot_access_clients_endpoint(self):
        unauthorized_client = APIClient()
        response = unauthorized_client.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_endpoint_returns_analytics(self):
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_keys = {
            'clients_count',
            'active_clients_count',
            'services_count',
            'active_services_count',
            'appointments_count',
            'employees_count',
            'completed_count',
            'cancelled_count',
            'total_revenue',
            'average_check',
            'revenue_appointments_count',
            'status_counts',
            'popular_services',
            'employee_workload',
        }
        self.assertEqual(set(response.data.keys()), expected_keys)
        self.assertEqual(response.data['clients_count'], 1)
        self.assertEqual(response.data['services_count'], 1)
        self.assertEqual(response.data['appointments_count'], 1)
        self.assertEqual(response.data['completed_count'], 0)
        self.assertEqual(response.data['cancelled_count'], 0)
        self.assertEqual(Decimal(str(response.data['total_revenue'])), Decimal('0.00'))
        self.assertEqual(Decimal(str(response.data['average_check'])), Decimal('0.00'))
        self.assertEqual(response.data['revenue_appointments_count'], 0)

        self.assertEqual(response.data['status_counts'][0]['status'], 'Підтверджено')
        self.assertEqual(response.data['status_counts'][0]['total'], 1)
        self.assertEqual(response.data['popular_services'][0]['service_name'], self.service.name)
        self.assertEqual(response.data['popular_services'][0]['total'], 1)
        self.assertEqual(
            response.data['employee_workload'][0]['employee_username'],
            self.employee.username,
        )
        self.assertEqual(response.data['employee_workload'][0]['total'], 1)

    def test_employee_dashboard_shows_only_own_appointments(self):
        user_model = get_user_model()
        colleague = user_model.objects.create_user(
            username='employee_3',
            password='testpass123',
            role=UserRole.EMPLOYEE,
            organization=self.organization,
        )
        Appointment.objects.create(
            client=self.client_entity,
            service=self.service,
            employee=colleague,
            created_by=self.user,
            organization=self.organization,
            appointment_date=date(2026, 4, 30),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status=AppointmentStatus.PLANNED,
        )

        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['appointments_count'], 1)
        self.assertEqual(response.data['status_counts'][0]['status'], 'Підтверджено')
        self.assertEqual(response.data['status_counts'][0]['total'], 1)
        self.assertEqual(response.data['employee_workload'][0]['employee_username'], self.employee.username)

    def test_dashboard_endpoint_returns_revenue_for_completed_paid_appointments_only(self):
        Appointment.objects.create(
            client=self.client_entity,
            service=self.service,
            employee=self.employee,
            created_by=self.user,
            organization=self.organization,
            appointment_date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=AppointmentStatus.COMPLETED,
            actual_price='100.00',
        )
        Appointment.objects.create(
            client=self.client_entity,
            service=self.service,
            employee=self.employee,
            created_by=self.user,
            organization=self.organization,
            appointment_date=date(2026, 5, 2),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status=AppointmentStatus.COMPLETED,
            actual_price='200.00',
        )
        Appointment.objects.create(
            client=self.client_entity,
            service=self.service,
            employee=self.employee,
            created_by=self.user,
            organization=self.organization,
            appointment_date=date(2026, 5, 3),
            start_time=time(11, 0),
            end_time=time(12, 0),
            status=AppointmentStatus.COMPLETED,
            actual_price=None,
        )
        Appointment.objects.create(
            client=self.client_entity,
            service=self.service,
            employee=self.employee,
            created_by=self.user,
            organization=self.organization,
            appointment_date=date(2026, 5, 4),
            start_time=time(12, 0),
            end_time=time(13, 0),
            status=AppointmentStatus.CANCELLED,
            actual_price='500.00',
        )
        Appointment.objects.create(
            client=self.client_entity,
            service=self.service,
            employee=self.employee,
            created_by=self.user,
            organization=self.organization,
            appointment_date=date(2026, 5, 5),
            start_time=time(13, 0),
            end_time=time(14, 0),
            status=AppointmentStatus.PLANNED,
            actual_price='700.00',
        )
        Appointment.objects.create(
            client=self.other_client,
            service=self.other_service,
            employee=self.other_employee,
            created_by=self.other_employee,
            organization=self.other_organization,
            appointment_date=date(2026, 5, 6),
            start_time=time(14, 0),
            end_time=time(15, 0),
            status=AppointmentStatus.COMPLETED,
            actual_price='900.00',
        )

        response = self.client.get('/api/dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data['total_revenue'])), Decimal('300.00'))
        self.assertEqual(Decimal(str(response.data['average_check'])), Decimal('150.00'))
        self.assertEqual(response.data['revenue_appointments_count'], 2)

    def test_employee_dashboard_revenue_uses_only_own_completed_paid_appointments(self):
        user_model = get_user_model()
        colleague = user_model.objects.create_user(
            username='employee_4',
            password='testpass123',
            role=UserRole.EMPLOYEE,
            organization=self.organization,
        )
        Appointment.objects.create(
            client=self.client_entity,
            service=self.service,
            employee=self.employee,
            created_by=self.user,
            organization=self.organization,
            appointment_date=date(2026, 5, 7),
            start_time=time(9, 0),
            end_time=time(10, 0),
            status=AppointmentStatus.COMPLETED,
            actual_price='75.00',
        )
        Appointment.objects.create(
            client=self.client_entity,
            service=self.service,
            employee=colleague,
            created_by=self.user,
            organization=self.organization,
            appointment_date=date(2026, 5, 8),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status=AppointmentStatus.COMPLETED,
            actual_price='300.00',
        )

        self.client.force_authenticate(user=self.employee)
        response = self.client.get('/api/dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['appointments_count'], 2)
        self.assertEqual(Decimal(str(response.data['total_revenue'])), Decimal('75.00'))
        self.assertEqual(Decimal(str(response.data['average_check'])), Decimal('75.00'))
        self.assertEqual(response.data['revenue_appointments_count'], 1)
