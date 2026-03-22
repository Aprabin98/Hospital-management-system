from django.test import TestCase
from django.urls import reverse

from payments.models import Payment
from users.models import PatientProfile, User


class PaymentsSmokeTests(TestCase):
	def setUp(self):
		self.patient_user = User.objects.create_user(
			email='patient.pay@example.com',
			username='patient_pay',
			password='pass1234',
			role='PATIENT',
			is_active=True,
		)
		self.patient_profile, _ = PatientProfile.objects.get_or_create(
			user=self.patient_user,
			defaults={'full_name': 'Patient Pay'},
		)

		self.other_patient_user = User.objects.create_user(
			email='other.pay@example.com',
			username='other_pay',
			password='pass1234',
			role='PATIENT',
			is_active=True,
		)
		self.other_patient_profile, _ = PatientProfile.objects.get_or_create(
			user=self.other_patient_user,
			defaults={'full_name': 'Other Pay'},
		)

		self.admin_user = User.objects.create_user(
			email='admin.pay@example.com',
			username='admin_pay',
			password='pass1234',
			role='ADMIN',
			is_active=True,
		)

		self.payment = Payment.objects.create(
			payment_type='LAB_TEST',
			patient=self.patient_profile,
			amount=1000,
			status='UNPAID',
		)

	def test_patient_cannot_view_other_patient_payment(self):
		self.client.force_login(self.other_patient_user)
		response = self.client.get(reverse('payments:payment_detail', args=[self.payment.id]), follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Access denied')

	def test_admin_can_mark_payment_paid(self):
		self.client.force_login(self.admin_user)
		response = self.client.post(
			reverse('payments:mark_paid', args=[self.payment.id]),
			{'payment_method': 'CASH', 'notes': 'Collected at desk'},
			follow=True,
		)
		self.assertEqual(response.status_code, 200)
		self.payment.refresh_from_db()
		self.assertEqual(self.payment.status, 'PAID')
