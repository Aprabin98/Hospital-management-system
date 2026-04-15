from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import DrugInteraction


class DrugInteractionApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.doctor_user = user_model.objects.create_user(
            email='doctor.phase3@example.com',
            username='phase3doc',
            password='pass1234',
            role='DOCTOR',
            is_active=True,
        )

        DrugInteraction.objects.create(
            drug_a='Warfarin',
            drug_b='Aspirin',
            severity=DrugInteraction.SEVERITY_MAJOR,
            description='High bleeding risk.',
            management='Avoid combination or monitor INR closely.',
            source='Internal test data',
            is_active=True,
        )

    def test_doctor_can_check_interactions(self):
        self.client.force_login(self.doctor_user)
        response = self.client.get(
            reverse('drug_checker:check_interactions'),
            {'medicines': ['Warfarin', 'Aspirin']},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['interactions_found'], 1)
        self.assertEqual(payload['worst_severity'], DrugInteraction.SEVERITY_MAJOR)

    def test_non_doctor_is_forbidden(self):
        user_model = get_user_model()
        patient_user = user_model.objects.create_user(
            email='patient.phase3@example.com',
            username='phase3patient',
            password='pass1234',
            role='PATIENT',
            is_active=True,
        )
        self.client.force_login(patient_user)
        response = self.client.get(reverse('drug_checker:check_interactions'))
        self.assertEqual(response.status_code, 403)
