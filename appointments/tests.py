from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from clinical.models import Doctor, DoctorLeave
from users.models import PatientProfile, User


class AppointmentsSmokeTests(TestCase):
	def setUp(self):
		self.patient_user = User.objects.create_user(
			email='patient.appt@example.com',
			username='patient_appt',
			password='pass1234',
			role='PATIENT',
			is_active=True,
		)
		self.patient_profile, _ = PatientProfile.objects.get_or_create(
			user=self.patient_user,
			defaults={'full_name': 'Patient Appt'},
		)

		self.other_patient_user = User.objects.create_user(
			email='other.appt@example.com',
			username='other_appt',
			password='pass1234',
			role='PATIENT',
			is_active=True,
		)
		self.other_patient_profile, _ = PatientProfile.objects.get_or_create(
			user=self.other_patient_user,
			defaults={'full_name': 'Other Appt'},
		)

		self.doctor_user = User.objects.create_user(
			email='doctor.appt@example.com',
			username='doctor_appt',
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
			status='CONFIRMED',
		)

	def test_patient_can_view_own_appointment_detail(self):
		self.client.force_login(self.patient_user)
		response = self.client.get(reverse('appointments:appointment_detail', args=[self.appointment.id]))
		self.assertEqual(response.status_code, 200)

	def test_patient_cannot_view_other_patient_appointment_detail(self):
		self.client.force_login(self.other_patient_user)
		response = self.client.get(reverse('appointments:appointment_detail', args=[self.appointment.id]), follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Access denied')

	def test_no_show_dashboard_access_for_doctor(self):
		self.client.force_login(self.doctor_user)
		response = self.client.get(reverse('appointments:no_show_risk_dashboard'))
		self.assertEqual(response.status_code, 200)
		self.assertIn('items', response.json())

	def test_book_step3_rejects_doctor_leave_date(self):
		self.client.force_login(self.patient_user)
		tomorrow = date.today() + timedelta(days=1)
		DoctorLeave.objects.create(doctor=self.doctor, date=tomorrow, reason='Personal')

		session = self.client.session
		session['booking_specialization'] = 1
		session['booking_doctor'] = self.doctor.id
		session.save()

		response = self.client.post(
			reverse('appointments:book_step3'),
			{'appointment_date': tomorrow.isoformat()},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Doctor is on leave on this date')
