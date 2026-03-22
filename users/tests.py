from django.test import TestCase
from django.urls import reverse

from users.models import User


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
