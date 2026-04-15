from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from clinical.models import Doctor
from reviews.models import Review
from users.models import PatientProfile, User


class ReviewsFlowTests(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            email='review.patient@example.com',
            username='review_patient',
            password='pass1234',
            role='PATIENT',
            is_active=True,
        )
        self.patient_profile, _ = PatientProfile.objects.get_or_create(
            user=self.patient_user,
            defaults={'full_name': 'Review Patient'},
        )

        self.other_patient_user = User.objects.create_user(
            email='review.otherpatient@example.com',
            username='review_other_patient',
            password='pass1234',
            role='PATIENT',
            is_active=True,
        )
        self.other_patient_profile, _ = PatientProfile.objects.get_or_create(
            user=self.other_patient_user,
            defaults={'full_name': 'Other Review Patient'},
        )

        self.doctor_user = User.objects.create_user(
            email='review.doctor@example.com',
            username='review_doctor',
            password='pass1234',
            role='DOCTOR',
            is_active=True,
        )
        self.doctor = Doctor.objects.create(user=self.doctor_user)

        self.other_doctor_user = User.objects.create_user(
            email='review.otherdoctor@example.com',
            username='review_other_doctor',
            password='pass1234',
            role='DOCTOR',
            is_active=True,
        )
        self.other_doctor = Doctor.objects.create(user=self.other_doctor_user)

        self.admin_user = User.objects.create_user(
            email='review.admin@example.com',
            username='review_admin',
            password='pass1234',
            role='ADMIN',
            is_active=True,
            is_staff=True,
        )

        self.completed_appointment = Appointment.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(9, 30),
            status='COMPLETED',
        )

        self.pending_appointment = Appointment.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
            status='PENDING',
        )

    def test_patient_can_create_review_only_for_completed_appointment(self):
        self.client.force_login(self.patient_user)

        blocked = self.client.post(
            reverse('reviews:create_review', args=[self.pending_appointment.id]),
            {'rating': 4, 'comment': 'Should fail'},
            follow=True,
        )
        self.assertEqual(blocked.status_code, 200)
        self.assertEqual(Review.objects.filter(appointment=self.pending_appointment).count(), 0)

        allowed = self.client.post(
            reverse('reviews:create_review', args=[self.completed_appointment.id]),
            {'rating': 5, 'comment': 'Great consultation'},
            follow=True,
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(Review.objects.filter(appointment=self.completed_appointment).count(), 1)

    def test_doctor_can_only_view_own_review_page(self):
        Review.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor,
            appointment=self.completed_appointment,
            rating=5,
            comment='Good',
        )

        self.client.force_login(self.doctor_user)
        own_page = self.client.get(reverse('reviews:doctor_reviews', args=[self.doctor.id]))
        self.assertEqual(own_page.status_code, 200)

        denied_page = self.client.get(reverse('reviews:doctor_reviews', args=[self.other_doctor.id]), follow=True)
        self.assertEqual(denied_page.status_code, 200)
        self.assertContains(denied_page, 'Access denied')

    def test_admin_can_view_any_doctor_reviews(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('reviews:doctor_reviews', args=[self.doctor.id]))
        self.assertEqual(response.status_code, 200)
