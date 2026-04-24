from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from payments.models import (
	DenialRework,
	InsuranceClaim,
	InsuranceVerification,
	Invoice,
	Payment,
)
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


class Phase7FinanceApiTests(TestCase):
	def setUp(self):
		self.api_client = APIClient()

		self.admin_user = User.objects.create_user(
			email='phase7.admin@example.com',
			username='phase7_admin',
			password='pass1234',
			role='ADMIN',
			is_active=True,
		)
		self.billing_user = User.objects.create_user(
			email='phase7.billing@example.com',
			username='phase7_billing',
			password='pass1234',
			role='BILLING_OFFICER',
			is_active=True,
		)
		self.insurance_user = User.objects.create_user(
			email='phase7.insurance@example.com',
			username='phase7_insurance',
			password='pass1234',
			role='INSURANCE_COORDINATOR',
			is_active=True,
		)
		self.patient_user = User.objects.create_user(
			email='phase7.patient@example.com',
			username='phase7_patient',
			password='pass1234',
			role='PATIENT',
			is_active=True,
		)

		self.patient_profile = self.patient_user.patient_profile
		self.patient_profile.full_name = 'Phase7 Patient'
		self.patient_profile.save(update_fields=['full_name'])

		self.insurance_verification = InsuranceVerification.objects.create(
			patient=self.patient_profile,
			provider_name='NIBL Insurance',
			policy_number='NIBL-001',
			plan_name='Gold Plus',
			coverage_percent=80,
			status='VERIFIED',
			valid_until=timezone.now().date() + timezone.timedelta(days=30),
		)

		self.invoice = Invoice.objects.create(
			invoice_number='INV-TEST-0001',
			invoice_type='PROFORMA',
			patient=self.patient_profile,
			subtotal=1000,
			tax_amount=100,
			discount_amount=0,
			total_amount=1100,
			patient_amount=1100,
			created_by=self.admin_user,
		)

		self.claim = InsuranceClaim.objects.create(
			claim_number='CLM-TEST-0001',
			invoice=self.invoice,
			patient=self.patient_profile,
			insurance_verification=self.insurance_verification,
			claimed_amount=1100,
			status='DRAFT',
		)

	def test_invoice_finalize_and_mark_paid_flow(self):
		self.api_client.force_authenticate(user=self.billing_user)

		finalize_response = self.api_client.post(
			reverse('api:invoice-finalize', args=[self.invoice.id]),
			{},
			format='json',
		)
		self.assertEqual(finalize_response.status_code, 200)

		self.invoice.refresh_from_db()
		self.assertEqual(self.invoice.invoice_type, 'FINAL')
		self.assertEqual(self.invoice.status, 'ISSUED')

		mark_paid_response = self.api_client.post(
			reverse('api:invoice-mark-paid', args=[self.invoice.id]),
			{'amount_paid': 1100},
			format='json',
		)
		self.assertEqual(mark_paid_response.status_code, 200)

		self.invoice.refresh_from_db()
		self.assertEqual(self.invoice.status, 'PAID')
		self.assertEqual(float(self.invoice.amount_paid), 1100.0)

	def test_patient_cannot_access_finance_dashboard(self):
		self.api_client.force_authenticate(user=self.patient_user)
		response = self.api_client.get(reverse('api:finance_dashboard'))
		self.assertEqual(response.status_code, 403)

	def test_insurance_rejection_creates_denial_rework(self):
		self.api_client.force_authenticate(user=self.insurance_user)

		submit_response = self.api_client.post(
			reverse('api:claim-submit', args=[self.claim.id]),
			{'submission_reference': 'SUB-001'},
			format='json',
		)
		self.assertEqual(submit_response.status_code, 200)

		reject_response = self.api_client.post(
			reverse('api:claim-reject', args=[self.claim.id]),
			{'reason': 'Missing attachment'},
			format='json',
		)
		self.assertEqual(reject_response.status_code, 200)

		self.claim.refresh_from_db()
		self.assertEqual(self.claim.status, 'REJECTED')
		self.assertTrue(DenialRework.objects.filter(claim=self.claim, status='PENDING_REVIEW').exists())

	def test_denial_rework_assign_and_resubmit(self):
		self.claim.status = 'REJECTED'
		self.claim.save(update_fields=['status'])
		rework = DenialRework.objects.create(
			claim=self.claim,
			original_denial_reason='Missing docs',
			status='PENDING_REVIEW',
		)

		self.api_client.force_authenticate(user=self.insurance_user)
		assign_response = self.api_client.post(
			reverse('api:denial_rework-assign', args=[rework.id]),
			{'assigned_to_id': self.billing_user.id},
			format='json',
		)
		self.assertEqual(assign_response.status_code, 200)

		rework.refresh_from_db()
		self.assertEqual(rework.status, 'UNDER_CORRECTION')
		self.assertEqual(rework.assigned_to_id, self.billing_user.id)

		self.api_client.force_authenticate(user=self.billing_user)
		resubmit_response = self.api_client.post(
			reverse('api:denial_rework-resubmit', args=[rework.id]),
			{
				'correction_notes': 'Added missing clinical summary',
				'submission_notes': 'Resubmitted with corrected package',
			},
			format='json',
		)
		self.assertEqual(resubmit_response.status_code, 200)

		rework.refresh_from_db()
		self.claim.refresh_from_db()
		self.assertEqual(rework.status, 'RESUBMITTED')
		self.assertEqual(self.claim.status, 'RESUBMITTED')

	def test_monthly_reconciliation_rejects_invalid_month(self):
		self.api_client.force_authenticate(user=self.admin_user)
		response = self.api_client.get(
			reverse('api:finance_reconciliation_monthly'),
			{'year': 2026, 'month': 13},
		)
		self.assertEqual(response.status_code, 400)
