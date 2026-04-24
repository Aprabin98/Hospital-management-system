from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from clinical.models import Doctor, Specialization
from surgery.models import OTSchedule
from users.models import User


class SurgeryApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='sur.admin@example.com', username='sur_admin', password='pass1234', role='ADMIN', is_active=True)
        self.doctor_user = User.objects.create_user(email='sur.doctor@example.com', username='sur_doc', password='pass1234', role='DOCTOR', is_active=True)
        self.nurse_user = User.objects.create_user(email='sur.nurse@example.com', username='sur_nurse', password='pass1234', role='NURSE', is_active=True)
        self.patient_user = User.objects.create_user(email='sur.patient@example.com', username='sur_patient', password='pass1234', role='PATIENT', is_active=True)

        spec = Specialization.objects.create(name='General Surgery', description='General Surgery')
        self.doctor = Doctor.objects.create(user=self.doctor_user, specialization=spec, consultation_fee=0, experience_years=5, is_available=True)

        self.patient = self.patient_user.patient_profile
        self.patient.full_name = 'Surgery Patient'
        self.patient.save(update_fields=['full_name'])

    def test_doctor_can_create_ot_schedule(self):
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post('/api/surgery/schedules/', {
            'patient': self.patient.id,
            'surgeon': self.doctor.id,
            'procedure_name': 'Appendectomy',
            'ot_room': 'OT-1',
            'scheduled_start': timezone.now().isoformat(),
            'scheduled_end': (timezone.now() + timedelta(hours=2)).isoformat(),
            'status': 'SCHEDULED',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_nurse_cannot_write_procedure_note(self):
        schedule = OTSchedule.objects.create(
            patient=self.patient,
            surgeon=self.doctor,
            procedure_name='Appendectomy',
            ot_room='OT-1',
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=2),
            created_by=self.admin,
        )
        self.client.force_authenticate(user=self.nurse_user)
        response = self.client.put(f'/api/surgery/schedules/{schedule.id}/procedure-note/', {
            'procedure_steps': 'Incision and closure',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nurse_can_add_post_op_note(self):
        schedule = OTSchedule.objects.create(
            patient=self.patient,
            surgeon=self.doctor,
            procedure_name='Appendectomy',
            ot_room='OT-1',
            scheduled_start=timezone.now(),
            scheduled_end=timezone.now() + timedelta(hours=2),
            created_by=self.admin,
        )
        self.client.force_authenticate(user=self.nurse_user)
        response = self.client.post(f'/api/surgery/schedules/{schedule.id}/post-op-notes/', {
            'recovery_status': 'OBSERVATION',
            'pain_score': 4,
            'notes': 'Stable in recovery bay',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
