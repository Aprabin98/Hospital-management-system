import json
from unittest.mock import patch

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

	def test_patient_can_create_insurance(self):
		self.client.force_login(self.patient_user)
		response = self.client.post(
			reverse('payments:insurance_create'),
			{
				'provider_name': 'NIBL Insurance',
				'policy_number': 'POL-1001',
				'plan_name': 'Family Plan',
				'coverage_percent': 80,
			},
		)
		self.assertEqual(response.status_code, 201)

	@patch('payments.khalti_views.log_audit_event')
	@patch('payments.khalti_views.khalti_service.initiate_payment')
	def test_patient_can_initiate_khalti_payment_via_api(self, mock_initiate_payment, mock_log_audit_event):
		mock_initiate_payment.return_value = {'success': True, 'payment_url': 'https://khalti.test/pay'}
		self.client.force_login(self.patient_user)

		response = self.client.post(
			reverse('api:payments_khalti_initiate_api'),
			data=json.dumps({
				'payment_id': self.payment.id,
				'return_url': 'http://localhost:3000/billing/khalti-success',
			}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['payment_url'], 'https://khalti.test/pay')

	@patch('payments.khalti_views.khalti_service.verify_payment')
	def test_patient_can_verify_khalti_payment_via_api(self, mock_verify_payment):
		mock_verify_payment.return_value = {'success': True, 'status': 'Completed', 'mobile': '9800000000'}
		self.client.force_login(self.patient_user)

		response = self.client.post(
			reverse('api:payments_khalti_verify_api'),
			data=json.dumps({'pidx': 'pidx-123', 'payment_id': self.payment.id}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()['status'], 'Completed')
