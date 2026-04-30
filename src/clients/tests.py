from django.test import TestCase
from django.urls import reverse

from users.models import Organization, User, UserRole

from .models import Client


class ClientListPaginationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Client Org', slug='client-org')
        self.user = User.objects.create_user(
            username='client_manager',
            email='client_manager@example.com',
            password='StrongPass123!',
            role=UserRole.MANAGER,
            organization=self.organization,
        )

    def _create_clients(self, count, *, name_prefix='Client', is_active=True, start_index=0):
        for index in range(count):
            phone_index = start_index + index
            Client.objects.create(
                full_name=f'{name_prefix} {index:02d}',
                phone=f'+38050100{phone_index:04d}',
                email=f'{name_prefix.lower()}_{index:02d}@example.com',
                is_active=is_active,
                organization=self.organization,
                created_by=self.user,
            )

    def test_client_list_is_limited_to_page_size(self):
        self._create_clients(12)
        self.client.force_login(self.user)

        response = self.client.get(reverse('client_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(response.context['page_obj'].paginator.count, 12)

    def test_client_pagination_keeps_filter_query_params(self):
        self._create_clients(12, name_prefix='Filtered')
        self._create_clients(2, name_prefix='Inactive', is_active=False, start_index=100)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('client_list'),
            {'query': 'Filtered', 'is_active': 'true', 'page': '2'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'href="?query=Filtered&amp;is_active=true&amp;page=1"',
        )
        self.assertEqual(response.context['query_string'], 'query=Filtered&is_active=true')

    def test_invalid_page_does_not_crash(self):
        self._create_clients(12)
        self.client.force_login(self.user)

        response = self.client.get(reverse('client_list'), {'page': 'invalid'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].number, 1)

    def test_second_page_returns_different_clients(self):
        self._create_clients(12)
        self.client.force_login(self.user)

        first_page = self.client.get(reverse('client_list'), {'page': '1'})
        second_page = self.client.get(reverse('client_list'), {'page': '2'})

        first_page_ids = {client.pk for client in first_page.context['page_obj']}
        second_page_ids = {client.pk for client in second_page.context['page_obj']}

        self.assertEqual(len(first_page_ids), 10)
        self.assertEqual(len(second_page_ids), 2)
        self.assertTrue(first_page_ids.isdisjoint(second_page_ids))
