from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from clinical.models import Doctor, Specialization
from users.models import PatientProfile, User


class NoShowPredictorApiTests(TestCase):
    def setUp(self):
        self.specialization = Specialization.objects.create(name='Cardiology')

        self.doctor_user = User.objects.create_user(
            email='doctor@example.com',
            username='doctor',
            password='pass123',
            role='DOCTOR',
            is_active=True,
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization=self.specialization,
            consultation_fee=1000,
        )

        self.patient_user = User.objects.create_user(
            email='patient@example.com',
            username='patient',
            password='pass123',
            role='PATIENT',
            is_active=True,
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user, full_name='Patient One')

        self.reception_user = User.objects.create_user(
            email='reception@example.com',
            username='reception',
            password='pass123',
            role='RECEPTIONIST',
            is_active=True,
        )

    def test_patient_can_get_prediction(self):
        self.client.force_login(self.patient_user)
        url = reverse('appointments:predict_no_show_api')
        response = self.client.get(
            url,
            {'doctor_id': self.doctor.id, 'date': (date.today() + timedelta(days=1)).isoformat()},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('risk_score', payload)
        self.assertIn('risk_level', payload)

    def test_receptionist_requires_patient_id(self):
        self.client.force_login(self.reception_user)
        url = reverse('appointments:predict_no_show_api')
        response = self.client.get(
            url,
            {'doctor_id': self.doctor.id, 'date': (date.today() + timedelta(days=2)).isoformat()},
        )
        self.assertEqual(response.status_code, 400)
