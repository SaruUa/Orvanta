from django.test import TestCase
from django.urls import reverse

from users.models import Organization, User, UserRole

from .models import AuditActionType, AuditEntityType, AuditLog


class AuditLogListPaginationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Audit Org', slug='audit-org')
        self.other_organization = Organization.objects.create(
            name='Other Audit Org',
            slug='other-audit-org',
        )
        self.admin_user = User.objects.create_user(
            username='audit_admin',
            email='audit_admin@example.com',
            password='StrongPass123!',
            role=UserRole.ADMIN,
            organization=self.organization,
        )
        self.other_admin_user = User.objects.create_user(
            username='other_audit_admin',
            email='other_audit_admin@example.com',
            password='StrongPass123!',
            role=UserRole.ADMIN,
            organization=self.other_organization,
        )

    def test_audit_log_list_is_paginated_and_organization_scoped(self):
        for index in range(25):
            AuditLog.objects.create(
                user=self.admin_user,
                action_type=AuditActionType.CREATE,
                entity_type=AuditEntityType.CLIENT,
                entity_id=index + 1,
                description=f'Audit log {index:02d}',
                organization=self.organization,
            )
            AuditLog.objects.create(
                user=self.other_admin_user,
                action_type=AuditActionType.CREATE,
                entity_type=AuditEntityType.CLIENT,
                entity_id=index + 1,
                description=f'Other audit log {index:02d}',
                organization=self.other_organization,
            )
        self.client.force_login(self.admin_user)

        filter_params = {
            'action_type': AuditActionType.CREATE,
            'entity_type': AuditEntityType.CLIENT,
        }
        first_page = self.client.get(reverse('audit_log_list'), filter_params)
        second_page = self.client.get(
            reverse('audit_log_list'),
            {**filter_params, 'page': '2'},
        )

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.context['page_obj'].paginator.count, 25)
        self.assertEqual(len(first_page.context['page_obj']), 20)
        self.assertEqual(len(second_page.context['page_obj']), 5)
        self.assertTrue(
            all(log.organization == self.organization for log in first_page.context['page_obj'])
        )
        self.assertTrue(
            all(log.organization == self.organization for log in second_page.context['page_obj'])
        )
