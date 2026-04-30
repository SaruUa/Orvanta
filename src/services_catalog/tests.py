from django.test import TestCase
from django.urls import reverse

from users.models import Organization, User, UserRole

from .models import Service, ServiceCategory


class ServiceListPaginationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Service Org', slug='service-org')
        self.user = User.objects.create_user(
            username='service_manager',
            email='service_manager@example.com',
            password='StrongPass123!',
            role=UserRole.MANAGER,
            organization=self.organization,
        )
        self.category = ServiceCategory.objects.create(
            name='Service Category',
            organization=self.organization,
        )

    def test_service_list_is_limited_to_page_size(self):
        for index in range(12):
            Service.objects.create(
                category=self.category,
                name=f'Service {index:02d}',
                price='100.00',
                duration_minutes=30,
                organization=self.organization,
            )
        self.client.force_login(self.user)

        response = self.client.get(reverse('service_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(response.context['page_obj'].paginator.count, 12)
