from django.test import TestCase
from django.urls import reverse

from .models import Organization, User, UserRole


class SignupFlowTests(TestCase):
    def test_signup_creates_admin_user_organization_and_logs_in(self):
        response = self.client.post(
            reverse('signup'),
            data={
                'username': 'new_owner',
                'email': 'owner@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
                'organization_name': 'Ink Owner Studio',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('home'))

        user = User.objects.get(username='new_owner')
        organization = Organization.objects.get(name='Ink Owner Studio')

        self.assertEqual(user.organization, organization)
        self.assertEqual(user.role, UserRole.ADMIN)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(response.wsgi_request.user.pk, user.pk)

    def test_signup_generates_unique_organization_slug(self):
        Organization.objects.create(name='Alpha Org', slug='alpha-org')

        self.client.post(
            reverse('signup'),
            data={
                'username': 'owner_two',
                'email': 'owner2@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
                'organization_name': 'Alpha---Org',
            },
        )

        organization = Organization.objects.get(name='Alpha---Org')
        self.assertNotEqual(organization.slug, 'alpha-org')
        self.assertTrue(organization.slug.startswith('alpha-org'))


class OrganizationUserCreateTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Org One', slug='org-one')
        self.other_organization = Organization.objects.create(name='Org Two', slug='org-two')

        self.admin_user = User.objects.create_user(
            username='org_admin',
            email='org_admin@example.com',
            password='StrongPass123!',
            role=UserRole.ADMIN,
            organization=self.organization,
        )
        self.manager_user = User.objects.create_user(
            username='org_manager',
            email='org_manager@example.com',
            password='StrongPass123!',
            role=UserRole.MANAGER,
            organization=self.organization,
        )
        self.employee_user = User.objects.create_user(
            username='org_employee',
            email='org_employee@example.com',
            password='StrongPass123!',
            role=UserRole.EMPLOYEE,
            organization=self.organization,
        )

    def test_admin_can_create_manager_and_employee(self):
        self.client.force_login(self.admin_user)

        cases = (
            (UserRole.MANAGER, 'new_manager', 'new_manager@example.com'),
            (UserRole.EMPLOYEE, 'new_employee', 'new_employee@example.com'),
        )
        for role, username, email in cases:
            response = self.client.post(
                reverse('user_create'),
                data={
                    'username': username,
                    'email': email,
                    'password1': 'StrongPass123!',
                    'password2': 'StrongPass123!',
                    'role': role,
                },
            )

            self.assertRedirects(response, reverse('user_list'))
            created_user = User.objects.get(username=username)
            self.assertEqual(created_user.organization, self.organization)
            self.assertEqual(created_user.role, role)
            self.assertTrue(created_user.is_active)
            self.assertFalse(created_user.is_staff)
            self.assertFalse(created_user.is_superuser)

    def test_admin_post_cannot_override_security_fields(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('user_create'),
            data={
                'username': 'safe_user',
                'email': 'safe_user@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
                'role': UserRole.MANAGER,
                'organization': self.other_organization.pk,
                'is_staff': True,
                'is_superuser': True,
            },
        )

        self.assertRedirects(response, reverse('user_list'))
        created_user = User.objects.get(username='safe_user')
        self.assertEqual(created_user.organization, self.organization)
        self.assertFalse(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)

    def test_manager_and_employee_cannot_use_create_endpoint(self):
        for user, username, email in (
            (self.manager_user, 'blocked_from_manager', 'blocked_from_manager@example.com'),
            (self.employee_user, 'blocked_from_employee', 'blocked_from_employee@example.com'),
        ):
            self.client.force_login(user)

            get_response = self.client.get(reverse('user_create'))
            self.assertRedirects(get_response, reverse('home'))

            post_response = self.client.post(
                reverse('user_create'),
                data={
                    'username': username,
                    'email': email,
                    'password1': 'StrongPass123!',
                    'password2': 'StrongPass123!',
                    'role': UserRole.EMPLOYEE,
                },
            )
            self.assertRedirects(post_response, reverse('home'))
            self.assertFalse(User.objects.filter(username=username).exists())

    def test_admin_cannot_create_user_with_disallowed_role(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('user_create'),
            data={
                'username': 'forbidden_admin',
                'email': 'forbidden_admin@example.com',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
                'role': UserRole.ADMIN,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='forbidden_admin').exists())
