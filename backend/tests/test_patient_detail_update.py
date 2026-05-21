from django.test import TestCase
from rest_framework.test import APIClient

from users.models import User, PatientProfile


class PatientDetailUpdateTests(TestCase):
    def test_admin_can_update_patient_date_of_birth(self):
        admin = User.objects.create_superuser(
            email='admin.update@example.com',
            username='admin_update',
            password='AdminPass123!',
        )
        patient = User.objects.create_user(
            email='patient.update@example.com',
            username='patient_update',
            password='PatientPass123!',
            role='PATIENT',
            is_active=True,
        )
        profile = PatientProfile.objects.get(user=patient)

        client = APIClient()
        client.force_authenticate(user=admin)

        response = client.patch(
            f'/api/patients/{profile.id}/',
            {'date_of_birth': '1992-08-15'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(str(profile.date_of_birth), '1992-08-15')
