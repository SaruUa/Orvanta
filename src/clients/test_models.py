from django.db import IntegrityError
from django.test import TestCase

from users.models import Organization, User

from .models import Client


class ClientModelTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Client Org', slug='client-org')
        self.admin = User.objects.create_user(
            username='admin', password='pass', organization=self.org, role='admin'
        )

    def _make_client(self, full_name='Тест Клієнт', phone='+380501234567'):
        return Client.objects.create(
            full_name=full_name,
            phone=phone,
            organization=self.org,
            created_by=self.admin,
        )

    def test_str_returns_full_name(self):
        client = self._make_client('Олена Іваненко')
        self.assertEqual(str(client), 'Олена Іваненко')

    def test_is_active_default_true(self):
        client = self._make_client()
        self.assertTrue(client.is_active)

    def test_unique_phone_per_organization(self):
        self._make_client(phone='+380501111111')
        with self.assertRaises(IntegrityError):
            self._make_client(phone='+380501111111', full_name='Інший Клієнт')

    def test_same_phone_allowed_in_different_organizations(self):
        org2 = Organization.objects.create(name='Інша Орг', slug='other-org')
        admin2 = User.objects.create_user(
            username='admin2', password='pass', organization=org2, role='admin'
        )
        self._make_client(phone='+380509999999')
        client2 = Client.objects.create(
            full_name='Клієнт Два',
            phone='+380509999999',
            organization=org2,
            created_by=admin2,
        )
        self.assertEqual(client2.phone, '+380509999999')

    def test_ordering_is_by_full_name(self):
        self._make_client('Яків Шевченко', '+380500000001')
        self._make_client('Аліна Бонд', '+380500000002')
        names = list(Client.objects.values_list('full_name', flat=True))
        self.assertEqual(names[0], 'Аліна Бонд')
        self.assertEqual(names[1], 'Яків Шевченко')
