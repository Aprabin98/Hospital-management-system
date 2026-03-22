from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditLog


class AuditTrailTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin_user = self.user_model.objects.create_user(
            email='admin_audit@example.com',
            username='admin_audit',
            password='StrongPass123!',
            role='ADMIN',
            is_active=True,
            is_staff=True,
        )

    def test_login_creates_audit_entry(self):
        response = self.client.post(
            reverse('users:login'),
            {'email': 'admin_audit@example.com', 'password': 'StrongPass123!'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AuditLog.objects.filter(action='LOGIN', actor=self.admin_user).exists())

    def test_admin_can_open_audit_log_page(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('audit:audit_log_list'))
        self.assertEqual(response.status_code, 200)

    def test_non_admin_cannot_open_audit_log_page(self):
        normal_user = self.user_model.objects.create_user(
            email='patient_audit@example.com',
            username='patient_audit',
            password='StrongPass123!',
            role='PATIENT',
            is_active=True,
        )
        self.client.force_login(normal_user)
        response = self.client.get(reverse('audit:audit_log_list'))
        self.assertEqual(response.status_code, 302)
