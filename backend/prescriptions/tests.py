from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from clinical.models import Doctor
from prescriptions.models import Pharmacy, Prescription
from users.models import PatientProfile, User


class PrescriptionFeatureTests(TestCase):
	def setUp(self):
		self.patient_user = User.objects.create_user(
			email='patient.rx@example.com',
			username='patient_rx',
			password='pass1234',
			role='PATIENT',
			is_active=True,
		)
		self.patient_profile, _ = PatientProfile.objects.get_or_create(
			user=self.patient_user,
			defaults={'full_name': 'Patient Rx'},
		)

		self.doctor_user = User.objects.create_user(
			email='doctor.rx@example.com',
			username='doctor_rx',
			password='pass1234',
			role='DOCTOR',
			is_active=True,
		)
		self.doctor = Doctor.objects.create(user=self.doctor_user)

		self.appointment = Appointment.objects.create(
			patient=self.patient_profile,
			doctor=self.doctor,
			date=date.today(),
			start_time=time(9, 0),
			end_time=time(9, 30),
			status='COMPLETED',
		)

		self.prescription = Prescription.objects.create(
			appointment=self.appointment,
			doctor=self.doctor,
			patient=self.patient_profile,
			total_refills_allowed=2,
		)

		self.receptionist_user = User.objects.create_user(
			email='rcp.rx@example.com',
			username='rcp_rx',
			password='pass1234',
			role='RECEPTIONIST',
			is_active=True,
		)

		self.pharmacy = Pharmacy.objects.create(name='City Pharmacy', location='Main Road')

	def test_patient_can_request_refill(self):
		self.client.force_login(self.patient_user)
		response = self.client.post(
			reverse('prescriptions:request_refill', args=[self.prescription.id]),
			{'reason': 'Medicine finished'},
		)
		self.assertEqual(response.status_code, 201)

	def test_doctor_can_approve_refill(self):
		self.client.force_login(self.patient_user)
		create_resp = self.client.post(
			reverse('prescriptions:request_refill', args=[self.prescription.id]),
			{'reason': 'Need more'},
		)
		refill_id = create_resp.json()['id']

		self.client.force_login(self.doctor_user)
		approve_resp = self.client.post(
			reverse('prescriptions:approve_refill', args=[refill_id]),
			{'approval_notes': 'Approved'},
		)
		self.assertEqual(approve_resp.status_code, 200)

	def test_receptionist_can_fill_approved_refill(self):
		self.client.force_login(self.patient_user)
		create_resp = self.client.post(
			reverse('prescriptions:request_refill', args=[self.prescription.id]),
			{'reason': 'Need more'},
		)
		refill_id = create_resp.json()['id']

		self.client.force_login(self.doctor_user)
		self.client.post(reverse('prescriptions:approve_refill', args=[refill_id]), {'approval_notes': 'ok'})

		self.client.force_login(self.receptionist_user)
		fill_resp = self.client.post(
			reverse('prescriptions:pharmacy_fill_refill', args=[refill_id]),
			{'pharmacy_id': self.pharmacy.id},
		)
		self.assertEqual(fill_resp.status_code, 200)
