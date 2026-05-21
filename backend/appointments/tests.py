from datetime import date, time, timedelta
import json

from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from appointments.models import Appointment, TriageAssessment, MedicalReportAnalysis, Queue, WaitingList
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

		self.reception_user = User.objects.create_user(
			email='reception.appt@example.com',
			username='reception_appt',
			password='pass1234',
			role='RECEPTIONIST',
			is_active=True,
		)

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

	def test_patient_can_submit_triage_and_get_priority(self):
		self.client.force_login(self.patient_user)
		response = self.client.post(
			reverse('appointments:triage_dashboard'),
			{
				'symptoms': 'I have chest pain and shortness of breath since morning',
				'duration_days': 1,
				'pain_level': 8,
				'has_fever': False,
				'has_breathing_issue': True,
				'has_chest_pain': True,
				'has_heavy_bleeding': False,
				'had_fainting_episode': False,
			},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(TriageAssessment.objects.count(), 1)
		triage = TriageAssessment.objects.first()
		self.assertIn(triage.priority, ['P1', 'P2', 'P3', 'P4'])
		self.assertGreaterEqual(triage.priority_score, 0)
		self.assertContains(response, 'Priority assigned')

	def test_receptionist_can_list_queue_via_api(self):
		Queue.objects.create(
			patient=self.patient_profile,
			doctor=self.doctor,
			status='WAITING',
			source='SCHEDULED',
			priority='P4',
		)

		self.client.force_login(self.reception_user)
		response = self.client.get(reverse('api:queue_list_api'))

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(len(payload), 1)
		self.assertEqual(payload[0]['patient_name'], self.patient_profile.full_name)

	def test_receptionist_can_create_queue_entry_via_api(self):
		self.client.force_login(self.reception_user)
		response = self.client.post(
			reverse('api:queue_list_api'),
			data=json.dumps({
				'patient_id': self.patient_profile.id,
				'doctor_id': self.doctor.id,
				'source': 'WALK_IN',
				'priority': 'P3',
				'notes': 'Front desk check-in',
			}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 201)
		payload = response.json()
		self.assertEqual(payload['patient_name'], self.patient_profile.full_name)
		self.assertTrue(payload['doctor_name'])

	def test_receptionist_can_manage_waiting_list_and_no_show_via_api(self):
		waiting = WaitingList.objects.create(
			patient=self.other_patient_profile,
			doctor=self.doctor,
			date=date.today(),
			priority=10,
			status='WAITING',
		)
		released_slot = Appointment.objects.create(
			patient=self.patient_profile,
			doctor=self.doctor,
			date=date.today(),
			start_time=time(10, 0),
			end_time=time(10, 30),
			status='CANCELLED',
		)

		self.client.force_login(self.reception_user)

		queue_response = self.client.get(reverse('api:appointments_waiting_list_queue_api'))
		self.assertEqual(queue_response.status_code, 200)
		self.assertIn('results', queue_response.json())

		priority_response = self.client.post(
			reverse('api:appointments_waiting_list_priority_api', args=[waiting.id]),
			data=json.dumps({'priority': 90}),
			content_type='application/json',
		)
		self.assertEqual(priority_response.status_code, 200)
		waiting.refresh_from_db()
		self.assertEqual(waiting.priority, 90)

		promote_response = self.client.post(reverse('api:appointments_waiting_list_promote_api', args=[waiting.id]))
		self.assertEqual(promote_response.status_code, 200)
		self.assertIn('promoted_appointment_id', promote_response.json())
		released_slot.refresh_from_db()
		self.assertEqual(released_slot.patient, self.other_patient_profile)
		self.assertEqual(released_slot.status, 'CONFIRMED')

		no_show_response = self.client.get(reverse('api:appointments_no_show_dashboard_api'))
		self.assertEqual(no_show_response.status_code, 200)
		self.assertIn('results', no_show_response.json())

		outcome_response = self.client.post(
			reverse('api:appointments_no_show_outcome_api', args=[self.appointment.id]),
			data=json.dumps({'outcome': 'no_show'}),
			content_type='application/json',
		)
		self.assertEqual(outcome_response.status_code, 200)
		self.appointment.refresh_from_db()
		self.assertEqual(self.appointment.status, 'NO_SHOW')

	def test_lab_technician_cannot_access_triage_dashboard(self):
		lab_user = User.objects.create_user(
			email='labtriage@example.com',
			username='lab_triage',
			password='pass1234',
			role='LAB_TECHNICIAN',
			is_active=True,
		)
		self.client.force_login(lab_user)
		response = self.client.get(reverse('appointments:triage_dashboard'), follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Access denied')

	def test_patient_can_upload_report_and_get_ai_analysis(self):
		self.client.force_login(self.patient_user)
		report_file = SimpleUploadedFile(
			'cbc_report.txt',
			b'Hemoglobin: 9.2\nWBC: 14000\nPlatelets: 210000\nGlucose: 180',
			content_type='text/plain',
		)

		response = self.client.post(
			reverse('appointments:report_reader_dashboard'),
			{'title': 'CBC test', 'report_file': report_file},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(MedicalReportAnalysis.objects.count(), 1)
		analysis = MedicalReportAnalysis.objects.first()
		self.assertEqual(analysis.patient, self.patient_profile)
		self.assertIn(analysis.risk_level, ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'])
		summary_lines = [line for line in (analysis.ai_summary or '').splitlines() if line.strip()]
		self.assertGreaterEqual(len(summary_lines), 8)
		self.assertContains(response, 'Report analyzed successfully')

	def test_doctor_can_access_report_reader_dashboard(self):
		self.client.force_login(self.doctor_user)
		response = self.client.get(reverse('appointments:report_reader_dashboard'))
		self.assertEqual(response.status_code, 200)

	def test_patient_can_view_own_analyzed_report_detail(self):
		analysis = MedicalReportAnalysis.objects.create(
			patient=self.patient_profile,
			title='Sample',
			report_file='appointments/reports/sample.txt',
			report_type='CBC',
			risk_level='MODERATE',
			ai_summary='Detected 1 abnormal marker.',
			abnormal_flags=[{'marker': 'Hemoglobin', 'value': 9.2, 'status': 'low', 'normal_range': '12 - 17.5'}],
			recommendations='Follow-up suggested.',
			created_by=self.patient_user,
		)

		self.client.force_login(self.patient_user)
		response = self.client.get(reverse('appointments:report_reader_detail', args=[analysis.id]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Read Summary')
		self.assertContains(response, 'Food Suggestions')
		self.assertContains(response, 'trained AI models')

	def test_patient_cannot_view_other_patient_analyzed_report_detail(self):
		analysis = MedicalReportAnalysis.objects.create(
			patient=self.other_patient_profile,
			title='Other sample',
			report_file='appointments/reports/sample2.txt',
			report_type='GENERAL',
			risk_level='LOW',
			ai_summary='No major issue.',
			abnormal_flags=[],
			recommendations='Routine follow-up.',
			created_by=self.other_patient_user,
		)

		self.client.force_login(self.patient_user)
		response = self.client.get(reverse('appointments:report_reader_detail', args=[analysis.id]), follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Access denied')
