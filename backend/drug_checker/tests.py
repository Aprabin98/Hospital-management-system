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


class DrugInteractionAdminApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            email='admin.drug@example.com',
            username='admindrug',
            password='pass1234',
            role='ADMIN',
            is_active=True,
            is_staff=True,
        )
        self.patient_user = user_model.objects.create_user(
            email='patient.drug@example.com',
            username='patientdrug',
            password='pass1234',
            role='PATIENT',
            is_active=True,
        )

        self.interaction = DrugInteraction.objects.create(
            drug_a='Metformin',
            drug_b='Cimetidine',
            severity=DrugInteraction.SEVERITY_MODERATE,
            description='May increase metformin levels.',
            management='Monitor glucose and renal function.',
            source='Test source',
            is_active=True,
        )

    def test_authenticated_user_can_list_interactions(self):
        self.client.force_login(self.patient_user)
        response = self.client.get('/api/drug-interactions/')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('results', payload)
        self.assertGreaterEqual(payload.get('count', 0), 1)

    def test_non_admin_cannot_create_interaction(self):
        self.client.force_login(self.patient_user)
        response = self.client.post(
            '/api/drug-interactions/',
            {
                'drug1': 'Warfarin',
                'drug2': 'Aspirin',
                'severity': 'MAJOR',
                'description': 'High bleeding risk.',
                'action': 'Avoid together',
            },
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_and_delete_interaction(self):
        self.client.force_login(self.admin_user)

        create_response = self.client.post(
            '/api/drug-interactions/',
            {
                'drug1': 'Warfarin',
                'drug2': 'Aspirin',
                'severity': 'MAJOR',
                'description': 'High bleeding risk.',
                'action': 'Avoid together',
            },
            content_type='application/json',
        )
        self.assertEqual(create_response.status_code, 201)
        created_id = create_response.json()['id']

        delete_response = self.client.delete(f'/api/drug-interactions/{created_id}/')
        self.assertEqual(delete_response.status_code, 204)
