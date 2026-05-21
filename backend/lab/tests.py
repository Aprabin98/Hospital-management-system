from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from clinical.models import Doctor
from lab.models import TestBooking, TestResult, TestTemplate
from lab.models import LabSample
from payments.models import Payment
from users.models import PatientProfile, User


class LabWorkflowTests(TestCase):
	def setUp(self):
		self.patient_user = User.objects.create_user(
			email='patient.lab@example.com',
			username='patient_lab',
			password='pass1234',
			role='PATIENT',
			is_active=True,
		)
		self.patient_profile, _ = PatientProfile.objects.get_or_create(
			user=self.patient_user,
			defaults={'full_name': 'Patient Lab'},
		)

		self.other_patient_user = User.objects.create_user(
			email='other.patient@example.com',
			username='other_patient',
			password='pass1234',
			role='PATIENT',
			is_active=True,
		)
		self.other_patient_profile, _ = PatientProfile.objects.get_or_create(
			user=self.other_patient_user,
			defaults={'full_name': 'Other Patient'},
		)

		self.doctor_user = User.objects.create_user(
			email='doctor.lab@example.com',
			username='doctor_lab',
			password='pass1234',
			role='DOCTOR',
			is_active=True,
		)
		self.doctor = Doctor.objects.create(user=self.doctor_user)

		self.other_doctor_user = User.objects.create_user(
			email='doctor.other@example.com',
			username='doctor_other',
			password='pass1234',
			role='DOCTOR',
			is_active=True,
		)
		self.other_doctor = Doctor.objects.create(user=self.other_doctor_user)

		self.admin_user = User.objects.create_user(
			email='admin.lab@example.com',
			username='admin_lab',
			password='pass1234',
			role='ADMIN',
			is_active=True,
		)

		self.reception_user = User.objects.create_user(
			email='reception.lab@example.com',
			username='reception_lab',
			password='pass1234',
			role='RECEPTIONIST',
			is_active=True,
		)

		self.tech_user = User.objects.create_user(
			email='tech.lab@example.com',
			username='tech_lab',
			password='pass1234',
			role='LAB_TECHNICIAN',
			is_active=True,
		)

		self.template = TestTemplate.objects.create(
			name='CBC Panel',
			price=500,
			duration_minutes=60,
			is_available=True,
		)

		self.booking = TestBooking.objects.create(
			patient=self.patient_profile,
			template=self.template,
			date=date.today(),
			amount=500,
			status='PROCESSING',
			payment_status='UNPAID',
		)
		self.result = TestResult.objects.create(
			booking=self.booking,
			filled_by=self.tech_user,
			notes='Initial result',
		)

	def test_doctor_cannot_view_unrelated_patient_reports(self):
		self.client.force_login(self.doctor_user)
		response = self.client.get(
			reverse('lab:patient_reports', args=[self.other_patient_profile.id]),
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Access denied', status_code=200)

	def test_doctor_can_view_related_patient_reports(self):
		Appointment.objects.create(
			patient=self.patient_profile,
			doctor=self.doctor,
			date=date.today(),
			start_time=time(10, 0),
			end_time=time(10, 30),
			status='COMPLETED',
		)

		self.client.force_login(self.doctor_user)
		response = self.client.get(reverse('lab:patient_reports', args=[self.patient_profile.id]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.patient_profile.full_name)

	def test_release_requires_verification_and_paid_status(self):
		self.client.force_login(self.admin_user)

		response = self.client.post(reverse('lab:release_result', args=[self.result.id]), follow=True)
		self.assertEqual(response.status_code, 200)
		self.result.refresh_from_db()
		self.assertFalse(self.result.is_released)

		self.result.is_verified = True
		self.result.verified_by = self.admin_user
		self.result.save(update_fields=['is_verified', 'verified_by'])

		payment = Payment.objects.filter(lab_booking=self.booking).first()
		if payment is None:
			payment = Payment.objects.create(
				payment_type='LAB_TEST',
				lab_booking=self.booking,
				patient=self.patient_profile,
				amount=self.booking.amount,
				status='UNPAID',
			)

		payment.status = 'PAID'
		payment.save(update_fields=['status'])
		self.booking.refresh_from_db()

		response = self.client.post(reverse('lab:release_result', args=[self.result.id]), follow=True)
		self.assertEqual(response.status_code, 200)
		self.result.refresh_from_db()
		self.booking.refresh_from_db()

		self.assertTrue(self.result.is_released)
		self.assertEqual(self.booking.status, 'COMPLETED')
		self.assertIsNotNone(self.booking.completed_at)

	def test_receptionist_can_release_verified_paid_result(self):
		self.result.is_verified = True
		self.result.verified_by = self.admin_user
		self.result.save(update_fields=['is_verified', 'verified_by'])

		payment = Payment.objects.filter(lab_booking=self.booking).first()
		if payment is None:
			payment = Payment.objects.create(
				payment_type='LAB_TEST',
				lab_booking=self.booking,
				patient=self.patient_profile,
				amount=self.booking.amount,
				status='UNPAID',
			)

		payment.status = 'PAID'
		payment.save(update_fields=['status'])

		self.client.force_login(self.reception_user)
		response = self.client.post(f'/api/lab/results/{self.result.id}/release/')

		self.assertEqual(response.status_code, 200)
		self.result.refresh_from_db()
		self.booking.refresh_from_db()
		self.assertTrue(self.result.is_released)
		self.assertEqual(self.booking.status, 'COMPLETED')

	def test_invalid_status_transition_is_blocked(self):
		self.booking.status = 'PENDING'
		self.booking.save(update_fields=['status'])

		self.client.force_login(self.tech_user)
		response = self.client.post(
			reverse('lab:update_booking_status', args=[self.booking.id]),
			{'status': 'PROCESSING'},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.booking.refresh_from_db()
		self.assertEqual(self.booking.status, 'PENDING')

	def test_lab_samples_api_includes_patient_and_test_metadata(self):
		LabSample.objects.create(
			result=self.result,
			barcode_id='BC-10001',
			status='COLLECTED',
			collected_by=self.tech_user,
		)

		self.client.force_login(self.admin_user)
		response = self.client.get('/api/lab/samples/')

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload['count'], 1)
		sample = payload['results'][0]
		self.assertEqual(sample['patient_name'], self.patient_profile.full_name)
		self.assertEqual(sample['test_name'], self.template.name)
		self.assertEqual(sample['booking_date'], str(self.booking.date))
