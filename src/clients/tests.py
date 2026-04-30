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


class ClientExportCsvTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='CSV Client Org', slug='csv-client-org')
        self.other_organization = Organization.objects.create(
            name='Other CSV Client Org',
            slug='other-csv-client-org',
        )
        self.user = User.objects.create_user(
            username='csv_client_manager',
            email='csv_client_manager@example.com',
            password='StrongPass123!',
            role=UserRole.MANAGER,
            organization=self.organization,
        )
        self.other_user = User.objects.create_user(
            username='csv_client_other_manager',
            email='csv_client_other_manager@example.com',
            password='StrongPass123!',
            role=UserRole.MANAGER,
            organization=self.other_organization,
        )

    def _csv_text(self, response):
        return response.content.decode('utf-8-sig')

    def test_authorized_user_gets_csv_for_current_organization_only(self):
        Client.objects.create(
            full_name='Іван Петренко',
            phone='+380501100001',
            email='ivan@example.com',
            organization=self.organization,
            created_by=self.user,
        )
        Client.objects.create(
            full_name='Чужий Клієнт',
            phone='+380501100002',
            email='external@example.com',
            organization=self.other_organization,
            created_by=self.other_user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('client_export_csv'))
        csv_text = self._csv_text(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertTrue(
            response['Content-Disposition'].startswith(
                'attachment; filename="clients_export_',
            )
        )
        self.assertIn('ID;ПІБ;Телефон;Email;Активний;Дата створення;Дата оновлення', csv_text)
        self.assertIn('Іван Петренко', csv_text)
        self.assertIn('ivan@example.com', csv_text)
        self.assertNotIn('Чужий Клієнт', csv_text)
        self.assertNotIn('external@example.com', csv_text)

    def test_client_export_respects_search_and_active_filters(self):
        Client.objects.create(
            full_name='Іван Активний',
            phone='+380501100003',
            is_active=True,
            organization=self.organization,
            created_by=self.user,
        )
        Client.objects.create(
            full_name='Іван Неактивний',
            phone='+380501100004',
            is_active=False,
            organization=self.organization,
            created_by=self.user,
        )
        Client.objects.create(
            full_name='Марія Активна',
            phone='+380501100005',
            is_active=True,
            organization=self.organization,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('client_export_csv'),
            {'query': 'Іван', 'is_active': 'true'},
        )
        csv_text = self._csv_text(response)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Іван Активний', csv_text)
        self.assertNotIn('Іван Неактивний', csv_text)
        self.assertNotIn('Марія Активна', csv_text)

    def test_unauthenticated_user_cannot_export_clients(self):
        response = self.client.get(reverse('client_export_csv'))

        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response.get('Content-Type'), 'text/csv; charset=utf-8')
