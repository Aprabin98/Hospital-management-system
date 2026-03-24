from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from clinical.models import Doctor, DoctorLeave
from users.models import User


class DoctorLeaveEditTests(TestCase):
	def setUp(self):
		self.doctor_user = User.objects.create_user(
			email='doctor.leave@example.com',
			username='doctor_leave',
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

		self.leave = DoctorLeave.objects.create(
			doctor=self.doctor,
			date=date.today() + timedelta(days=2),
			reason='Initial leave reason',
		)

	def test_doctor_can_edit_own_leave(self):
		self.client.force_login(self.doctor_user, backend='users.backends.EmailBackend')

		new_date = date.today() + timedelta(days=3)
		response = self.client.post(
			reverse('clinical:doctor_leave_edit', args=[self.leave.id]),
			{
				'date': new_date.isoformat(),
				'reason': 'Updated leave reason',
			},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.leave.refresh_from_db()
		self.assertEqual(self.leave.date, new_date)
		self.assertEqual(self.leave.reason, 'Updated leave reason')
		self.assertContains(response, 'Leave updated successfully')

	def test_doctor_cannot_edit_other_doctor_leave(self):
		other_leave = DoctorLeave.objects.create(
			doctor=self.other_doctor,
			date=date.today() + timedelta(days=4),
			reason='Other doctor leave',
		)
		self.client.force_login(self.doctor_user, backend='users.backends.EmailBackend')

		response = self.client.get(reverse('clinical:doctor_leave_edit', args=[other_leave.id]))
		self.assertEqual(response.status_code, 404)
