from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from inpatient.models import InpatientStay
from users.models import PatientProfile, User


class InpatientModelAndApiTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin_test@hms.test',
            username='admin_test',
            password='Admin@123456',
            role='ADMIN',
            is_active=True,
            is_staff=True,
        )

        self.pharmacist_user = User.objects.create_user(
            email='pharm_test@hms.test',
            username='pharm_test',
            password='Pharmacist@123456',
            role='PHARMACIST',
            is_active=True,
            is_staff=True,
        )

        self.patient_user = User.objects.create_user(
            email='patient_test@hms.test',
            username='patient_test',
            password='Patient@123456',
            role='PATIENT',
            is_active=True,
        )

        self.patient_profile = PatientProfile.objects.get(user=self.patient_user)
        self.patient_profile.full_name = 'Test Patient'
        self.patient_profile.save(update_fields=['full_name'])

    def test_length_of_stay_days_uses_discharge_date(self):
        stay = InpatientStay.objects.create(
            patient=self.patient_profile,
            admitted_by=self.admin_user,
            primary_diagnosis='Observation',
        )

        stay.admission_datetime = timezone.now() - timedelta(days=5)
        stay.actual_discharge_date = timezone.localdate() - timedelta(days=2)
        stay.save(update_fields=['admission_datetime', 'actual_discharge_date'])

        self.assertEqual(stay.length_of_stay_days, 3)

    def test_ipd_stays_requires_authentication(self):
        response = self.client.get('/api/ipd/stays/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ipd_stays_forbidden_for_pharmacist_role(self):
        self.client.force_authenticate(user=self.pharmacist_user)
        response = self.client.get('/api/ipd/stays/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_inpatient_stay(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'patient_id': self.patient_profile.id,
            'primary_diagnosis': 'Community acquired pneumonia',
            'admission_reason': 'Fever and respiratory distress',
        }

        response = self.client.post('/api/ipd/stays/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InpatientStay.objects.count(), 1)
        stay = InpatientStay.objects.first()
        self.assertEqual(stay.patient_id, self.patient_profile.id)
        self.assertEqual(stay.admitted_by_id, self.admin_user.id)
        self.assertEqual(stay.status, 'ADMITTED')

