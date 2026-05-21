from django.test import TestCase

from users.models import User, PatientProfile


class RegisterApiPatientProfileTests(TestCase):
    def test_register_api_saves_patient_profile_details(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': 'profile.patient@example.com',
                'password': 'StrongPass123!',
                'first_name': 'Profile',
                'last_name': 'Patient',
                'phone': '9812345678',
                'date_of_birth': '1995-06-15',
                'gender': 'F',
                'blood_group': 'O+',
                'address': 'Kathmandu, Nepal',
                'emergency_contact': '9841122334',
                'height': '165',
                'weight': '58',
            },
        )

        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email='profile.patient@example.com')
        profile = PatientProfile.objects.get(user=user)

        self.assertEqual(profile.full_name, 'Profile Patient')
        self.assertEqual(profile.phone, '9812345678')
        self.assertEqual(profile.gender, 'F')
        self.assertEqual(profile.blood_group, 'O+')
        self.assertEqual(profile.address, 'Kathmandu, Nepal')
        self.assertEqual(profile.emergency_contact, '9841122334')
        self.assertEqual(str(profile.date_of_birth), '1995-06-15')
        self.assertEqual(profile.height, 165.0)
        self.assertEqual(profile.weight, 58.0)