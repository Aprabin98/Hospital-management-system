from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.core.cache import cache

from users.models import User, TwoFactorCode


class UsersSmokeTests(TestCase):
	def test_login_page_loads(self):
		response = self.client.get(reverse('users:login'))
		self.assertEqual(response.status_code, 200)

	def test_dashboard_redirects_to_role_page(self):
		user = User.objects.create_user(
			email='patient.route@example.com',
			username='patient_route',
			password='pass1234',
			role='PATIENT',
			is_active=True,
		)
		self.client.force_login(user)

		response = self.client.get(reverse('users:dashboard'))

		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('users:patient_dashboard'), response.url)


@override_settings(
	EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
	TWO_FACTOR_REQUIRED_ROLES=['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'LAB_TECHNICIAN'],
)
class TwoFactorFlowTests(TestCase):
	def test_admin_login_redirects_to_2fa(self):
		admin_user = User.objects.create_user(
			email='admin.2fa@example.com',
			username='admin_2fa',
			password='pass1234',
			role='ADMIN',
			is_active=True,
			is_staff=True,
		)

		response = self.client.post(
			reverse('users:login'),
			{'email': admin_user.email, 'password': 'pass1234'},
		)

		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('users:two_factor_verify'), response.url)
		self.assertTrue(TwoFactorCode.objects.filter(user=admin_user, is_used=False).exists())

	def test_patient_login_does_not_require_2fa(self):
		patient_user = User.objects.create_user(
			email='patient.no2fa@example.com',
			username='patient_no2fa',
			password='pass1234',
			role='PATIENT',
			is_active=True,
		)

		response = self.client.post(
			reverse('users:login'),
			{'email': patient_user.email, 'password': 'pass1234'},
		)

		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('users:dashboard'), response.url)
		self.assertFalse(TwoFactorCode.objects.filter(user=patient_user).exists())


@override_settings(
	RATE_LIMIT_ENABLED=True,
	RATE_LIMIT_RULES={
		'/users/login/': {
			'method': 'POST',
			'limit': 1,
			'window_seconds': 60,
		}
	},
)
class RateLimitTests(TestCase):
	def setUp(self):
		cache.clear()

	def test_login_rate_limit_blocks_second_quick_attempt(self):
		first = self.client.post(
			reverse('users:login'),
			{'email': 'unknown@example.com', 'password': 'wrongpass'},
		)
		second = self.client.post(
			reverse('users:login'),
			{'email': 'unknown@example.com', 'password': 'wrongpass'},
		)

		self.assertEqual(first.status_code, 200)
		self.assertEqual(second.status_code, 429)
