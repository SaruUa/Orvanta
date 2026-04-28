from datetime import date, time

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from appointments.models import Appointment, AppointmentStatus
from clients.models import Client
from services_catalog.models import Service, ServiceCategory
from users.models import UserRole


class ReadOnlyApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='api_user',
            password='testpass123',
            role=UserRole.ADMIN,
        )

        self.employee = user_model.objects.create_user(
            username='employee_1',
            password='testpass123',
            role=UserRole.EMPLOYEE,
        )

        self.client.force_authenticate(user=self.user)

        self.client_entity = Client.objects.create(
            full_name='Іван Петренко',
            phone='+380501112233',
            email='ivan@example.com',
            created_by=self.user,
        )
        self.category = ServiceCategory.objects.create(name='Тату')
        self.service = Service.objects.create(
            category=self.category,
            name='Контур',
            description='Контурна робота',
            price='1200.00',
            duration_minutes=90,
        )
        self.appointment = Appointment.objects.create(
            client=self.client_entity,
            service=self.service,
            employee=self.employee,
            created_by=self.user,
            appointment_date=date(2026, 4, 28),
            start_time=time(12, 0),
            end_time=time(13, 30),
            status=AppointmentStatus.CONFIRMED,
        )

    def test_clients_list_and_detail(self):
        list_response = self.client.get('/api/clients/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data[0]['id'], self.client_entity.id)

        detail_response = self.client.get(f'/api/clients/{self.client_entity.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['full_name'], self.client_entity.full_name)

    def test_services_list_and_detail(self):
        list_response = self.client.get('/api/services/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data[0]['category_name'], self.category.name)

        detail_response = self.client.get(f'/api/services/{self.service.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['name'], self.service.name)
        self.assertEqual(detail_response.data['category_name'], self.category.name)

    def test_appointments_list_and_detail(self):
        list_response = self.client.get('/api/appointments/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        appointment_data = list_response.data[0]
        self.assertEqual(appointment_data['client_full_name'], self.client_entity.full_name)
        self.assertEqual(appointment_data['service_name'], self.service.name)
        self.assertEqual(appointment_data['employee_username'], self.employee.username)
        self.assertEqual(appointment_data['status'], AppointmentStatus.CONFIRMED)

        detail_response = self.client.get(f'/api/appointments/{self.appointment.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['id'], self.appointment.id)
        self.assertEqual(detail_response.data['client_full_name'], self.client_entity.full_name)
        self.assertEqual(detail_response.data['service_name'], self.service.name)
        self.assertEqual(detail_response.data['employee_username'], self.employee.username)
        self.assertEqual(detail_response.data['appointment_date'], '2026-04-28')
        self.assertEqual(detail_response.data['start_time'], '12:00:00')
        self.assertEqual(detail_response.data['end_time'], '13:30:00')

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

        self.assertEqual(response.data['status_counts'][0]['status'], 'Підтверджено')
        self.assertEqual(response.data['status_counts'][0]['total'], 1)
        self.assertEqual(response.data['popular_services'][0]['service_name'], self.service.name)
        self.assertEqual(response.data['popular_services'][0]['total'], 1)
        self.assertEqual(
            response.data['employee_workload'][0]['employee_username'],
            self.employee.username,
        )
        self.assertEqual(response.data['employee_workload'][0]['total'], 1)
