from django.test import TestCase, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse

from .decorators import (
    admin_required,
    employee_manager_admin_required,
    manager_or_admin_required,
    organization_required,
)
from .models import Organization, User, UserRole


# ── Допоміжна view для тестів ──────────────────────────────────────────────────

def dummy_view(request, *args, **kwargs):
    return HttpResponse('OK', status=200)


def _make_request(factory, user, url='/test/'):
    """Створює GET-запит з прив'язаним користувачем і сховищем повідомлень."""
    request = factory.get(url)
    request.user = user
    # Django messages middleware потрібен для messages.error() у декораторах
    request.session = {}
    messages = FallbackStorage(request)
    request._messages = messages
    return request


class AdminRequiredDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name='Test Org', slug='test-org')
        self.admin = User.objects.create_user(
            username='admin', password='pass', role=UserRole.ADMIN, organization=self.org
        )
        self.manager = User.objects.create_user(
            username='mgr', password='pass', role=UserRole.MANAGER, organization=self.org
        )
        self.employee = User.objects.create_user(
            username='emp', password='pass', role=UserRole.EMPLOYEE, organization=self.org
        )
        self.view = admin_required(dummy_view)

    def test_admin_can_access(self):
        request = _make_request(self.factory, self.admin)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_manager_is_redirected(self):
        request = _make_request(self.factory, self.manager)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)

    def test_employee_is_redirected(self):
        request = _make_request(self.factory, self.employee)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_is_redirected_to_login(self):
        from django.contrib.auth.models import AnonymousUser
        request = _make_request(self.factory, AnonymousUser())
        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])


class ManagerOrAdminRequiredDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name='Test Org 2', slug='test-org-2')
        self.admin = User.objects.create_user(
            username='admin2', password='pass', role=UserRole.ADMIN, organization=self.org
        )
        self.manager = User.objects.create_user(
            username='mgr2', password='pass', role=UserRole.MANAGER, organization=self.org
        )
        self.employee = User.objects.create_user(
            username='emp2', password='pass', role=UserRole.EMPLOYEE, organization=self.org
        )
        self.view = manager_or_admin_required(dummy_view)

    def test_admin_can_access(self):
        request = _make_request(self.factory, self.admin)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_manager_can_access(self):
        request = _make_request(self.factory, self.manager)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_employee_is_redirected(self):
        request = _make_request(self.factory, self.employee)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)


class EmployeeManagerAdminRequiredDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name='Test Org 3', slug='test-org-3')
        self.admin = User.objects.create_user(
            username='admin3', password='pass', role=UserRole.ADMIN, organization=self.org
        )
        self.manager = User.objects.create_user(
            username='mgr3', password='pass', role=UserRole.MANAGER, organization=self.org
        )
        self.employee = User.objects.create_user(
            username='emp3', password='pass', role=UserRole.EMPLOYEE, organization=self.org
        )
        self.view = employee_manager_admin_required(dummy_view)

    def test_admin_can_access(self):
        request = _make_request(self.factory, self.admin)
        self.assertEqual(self.view(request).status_code, 200)

    def test_manager_can_access(self):
        request = _make_request(self.factory, self.manager)
        self.assertEqual(self.view(request).status_code, 200)

    def test_employee_can_access(self):
        request = _make_request(self.factory, self.employee)
        self.assertEqual(self.view(request).status_code, 200)


class OrganizationRequiredDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name='Test Org 4', slug='test-org-4')
        self.user_with_org = User.objects.create_user(
            username='with_org', password='pass', organization=self.org
        )
        self.user_without_org = User.objects.create_user(
            username='no_org', password='pass'
        )
        self.view = organization_required(dummy_view)

    def test_user_with_org_can_access(self):
        request = _make_request(self.factory, self.user_with_org)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_user_without_org_is_redirected(self):
        request = _make_request(self.factory, self.user_without_org)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)

    def test_redirect_goes_to_home(self):
        request = _make_request(self.factory, self.user_without_org)
        response = self.view(request)
        self.assertIn('/', response['Location'])
