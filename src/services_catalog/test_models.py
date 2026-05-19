from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from users.models import Organization

from .models import Service, ServiceCategory


class ServiceCategoryModelTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Svc Org', slug='svc-org')

    def test_str_returns_name(self):
        cat = ServiceCategory(name='Волосся')
        self.assertEqual(str(cat), 'Волосся')

    def test_unique_category_name_per_organization(self):
        ServiceCategory.objects.create(name='Нігті', organization=self.org)
        with self.assertRaises(IntegrityError):
            ServiceCategory.objects.create(name='Нігті', organization=self.org)

    def test_same_category_name_in_different_orgs(self):
        org2 = Organization.objects.create(name='Org Two', slug='org-two')
        ServiceCategory.objects.create(name='Масаж', organization=self.org)
        cat2 = ServiceCategory.objects.create(name='Масаж', organization=org2)
        self.assertEqual(cat2.name, 'Масаж')


class ServiceModelTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Svc Org 2', slug='svc-org-2')
        self.category = ServiceCategory.objects.create(name='Брови', organization=self.org)

    def _make_service(self, name='Корекція', price=250, duration=30):
        return Service.objects.create(
            name=name,
            price=Decimal(str(price)),
            duration_minutes=duration,
            category=self.category,
            organization=self.org,
        )

    def test_str_returns_name(self):
        svc = self._make_service('Фарбування брів')
        self.assertEqual(str(svc), 'Фарбування брів')

    def test_is_active_default_true(self):
        svc = self._make_service()
        self.assertTrue(svc.is_active)

    def test_unique_service_name_per_org_and_category(self):
        self._make_service(name='Корекція брів')
        with self.assertRaises(IntegrityError):
            self._make_service(name='Корекція брів')

    def test_same_service_name_in_different_category(self):
        cat2 = ServiceCategory.objects.create(name='Вії', organization=self.org)
        self._make_service(name='Ламінування')
        svc2 = Service.objects.create(
            name='Ламінування',
            price=Decimal('600'),
            duration_minutes=60,
            category=cat2,
            organization=self.org,
        )
        self.assertEqual(svc2.name, 'Ламінування')

    def test_price_stored_correctly(self):
        svc = self._make_service(price=1250)
        self.assertEqual(svc.price, Decimal('1250'))
