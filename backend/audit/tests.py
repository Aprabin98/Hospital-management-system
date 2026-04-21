from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.core.cache import cache
from datetime import date, time

from audit.models import AuditLog
from audit.models import SystemSetting
from reviews.models import Review
from clinical.models import Specialization, Doctor
from appointments.models import Appointment


@override_settings(TWO_FACTOR_REQUIRED_ROLES=[])
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


@override_settings(
    RATE_LIMIT_ENABLED=True,
    RATE_LIMIT_RULES={
        '/users/login/': {
            'method': 'POST',
            'limit': 1,
            'window_seconds': 60,
        }
    },
    TWO_FACTOR_REQUIRED_ROLES=[],
)
class AuditSecurityEventsTests(TestCase):
    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='security.audit@example.com',
            username='security_audit',
            password='StrongPass123!',
            role='PATIENT',
            is_active=True,
        )

    def test_rate_limit_creates_security_audit_entry(self):
        self.client.post(
            reverse('users:login'),
            {'email': 'unknown@example.com', 'password': 'wrong'},
        )
        blocked = self.client.post(
            reverse('users:login'),
            {'email': 'unknown@example.com', 'password': 'wrong'},
        )

        self.assertEqual(blocked.status_code, 429)
        self.assertTrue(
            AuditLog.objects.filter(
                action='SECURITY',
                description__icontains='rate limit exceeded',
            ).exists()
        )


@override_settings(TWO_FACTOR_REQUIRED_ROLES=[])
class AuditCrudSignalTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.patient_user = user_model.objects.create_user(
            email='crud.patient@example.com',
            username='crud_patient',
            password='StrongPass123!',
            role='PATIENT',
            is_active=True,
        )
        self.doctor_user = user_model.objects.create_user(
            email='crud.doctor@example.com',
            username='crud_doctor',
            password='StrongPass123!',
            role='DOCTOR',
            is_active=True,
        )
        self.specialization = Specialization.objects.create(name='Cardiology')
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization=self.specialization,
            consultation_fee=500,
            phone='9800000000',
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient_user.patient_profile,
            doctor=self.doctor,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='COMPLETED',
        )

    def test_create_review_logs_create_event(self):
        self.client.force_login(self.patient_user)
        response = self.client.post(
            reverse('reviews:create_review', args=[self.appointment.id]),
            {'rating': 4, 'comment': 'Good consultation'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            AuditLog.objects.filter(
                action='CREATE',
                model_name='reviews.review',
            ).exists()
        )

    def test_delete_review_logs_delete_event(self):
        review = Review.objects.create(
            patient=self.patient_user.patient_profile,
            doctor=self.doctor,
            appointment=self.appointment,
            rating=5,
            comment='To be deleted',
        )
        review.delete()
        self.assertTrue(
            AuditLog.objects.filter(
                action='DELETE',
                model_name='reviews.review',
            ).exists()
        )


@override_settings(TWO_FACTOR_REQUIRED_ROLES=[])
class SystemSettingsApiTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin_user = self.user_model.objects.create_user(
            email='settings.admin@example.com',
            username='settings_admin',
            password='StrongPass123!',
            role='ADMIN',
            is_active=True,
            is_staff=True,
        )
        self.patient_user = self.user_model.objects.create_user(
            email='settings.patient@example.com',
            username='settings_patient',
            password='StrongPass123!',
            role='PATIENT',
            is_active=True,
        )

    def test_admin_can_read_system_settings(self):
        self.client.force_login(self.admin_user)

        response = self.client.get('/api/system/settings/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('hospitalName', response.json())

    def test_admin_can_update_system_settings(self):
        self.client.force_login(self.admin_user)

        response = self.client.put(
            '/api/system/settings/',
            {
                'hospitalName': 'City Care Hospital',
                'maintenanceMode': True,
                'maxConcurrentUsers': 250,
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        updated = SystemSetting.objects.get(pk=1)
        self.assertEqual(updated.hospital_name, 'City Care Hospital')
        self.assertTrue(updated.maintenance_mode)
        self.assertEqual(updated.max_concurrent_users, 250)

    def test_non_admin_cannot_access_system_settings(self):
        self.client.force_login(self.patient_user)

        response = self.client.get('/api/system/settings/')

        self.assertEqual(response.status_code, 403)
