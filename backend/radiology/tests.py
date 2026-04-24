from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from clinical.models import Doctor, Specialization
from radiology.models import ImagingCatalog, ImagingOrder, ImagingReport
from users.models import PatientProfile


class RadiologyApiTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin_user = self.user_model.objects.create_user(
            email='radiology.admin@example.com',
            username='radiology_admin',
            password='password123',
            role='ADMIN',
            is_active=True,
        )
        self.doctor_user = self.user_model.objects.create_user(
            email='radiology.doctor@example.com',
            username='radiology_doctor',
            password='password123',
            role='DOCTOR',
            is_active=True,
        )
        self.patient_user = self.user_model.objects.create_user(
            email='radiology.patient@example.com',
            username='radiology_patient',
            password='password123',
            role='PATIENT',
            is_active=True,
        )
        self.other_patient_user = self.user_model.objects.create_user(
            email='radiology.other@example.com',
            username='radiology_other',
            password='password123',
            role='PATIENT',
            is_active=True,
        )

        specialization = Specialization.objects.create(name='Radiology', description='Radiology and imaging')
        self.doctor_profile = Doctor.objects.create(
            user=self.doctor_user,
            specialization=specialization,
            consultation_fee=0,
            experience_years=5,
            is_available=True,
        )

        self.patient_profile = self.patient_user.patient_profile
        self.patient_profile.full_name = 'Radiology Patient'
        self.patient_profile.save(update_fields=['full_name'])

        self.other_patient_profile = self.other_patient_user.patient_profile
        self.other_patient_profile.full_name = 'Other Radiology Patient'
        self.other_patient_profile.save(update_fields=['full_name'])

        self.catalog_item = ImagingCatalog.objects.create(
            name='Chest X-Ray PA View',
            modality='XRAY',
            description='Standard chest radiograph for QA.',
            preparation='Remove metal objects.',
            price=900,
            turnaround_hours=4,
        )
        self.other_catalog_item = ImagingCatalog.objects.create(
            name='CT Head Without Contrast',
            modality='CT',
            description='Rapid head imaging for QA.',
            preparation='No specific preparation.',
            price=6500,
            turnaround_hours=6,
        )

        self.order = ImagingOrder.objects.create(
            patient=self.patient_profile,
            catalog_item=self.catalog_item,
            ordered_by=self.doctor_user,
            priority='URGENT',
            status='ORDERED',
            clinical_notes='Initial QA imaging order',
        )
        ImagingOrder.objects.create(
            patient=self.other_patient_profile,
            catalog_item=self.other_catalog_item,
            ordered_by=self.doctor_user,
            priority='ROUTINE',
            status='ORDERED',
            clinical_notes='Secondary QA imaging order',
        )

        self.client = APIClient()

    def test_patient_cannot_release_report(self):
        self.client.force_authenticate(user=self.patient_user)

        response = self.client.post(reverse('radiology:order_release', args=[self.order.id]), {}, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'Access denied.')

    def test_doctor_can_release_report_and_update_history(self):
        self.client.force_authenticate(user=self.doctor_user)

        report_response = self.client.put(
            reverse('radiology:order_report', args=[self.order.id]),
            {
                'findings': 'Mild bibasal haziness.',
                'impression': 'Possible early infective change.',
                'recommendation': 'Clinical correlation advised.',
                'is_critical': False,
            },
            format='json',
        )

        self.assertEqual(report_response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'REPORTED')
        self.assertIsNotNone(self.order.completed_at)

        release_response = self.client.post(reverse('radiology:order_release', args=[self.order.id]), {}, format='json')

        self.assertEqual(release_response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'RELEASED')
        self.assertIsNotNone(self.order.released_at)
        self.assertEqual(self.order.report.report_status, 'FINAL')
        self.assertIsNotNone(self.order.report.released_at)

        self.client.force_authenticate(user=self.patient_user)
        history_response = self.client.get(reverse('radiology:history'))

        self.assertEqual(history_response.status_code, 200)
        self.assertTrue(any(item['id'] == self.order.id for item in history_response.data))

    def test_history_visibility_scopes_to_authenticated_role(self):
        self.client.force_authenticate(user=self.doctor_user)

        missing_scope_response = self.client.get(reverse('radiology:history'))
        self.assertEqual(missing_scope_response.status_code, 400)
        self.assertEqual(missing_scope_response.data['detail'], 'patient_id is required for staff history lookup.')

        ImagingReport.objects.create(
            order=self.order,
            findings='QA findings',
            impression='QA impression',
            recommendation='QA recommendation',
            report_status='FINAL',
            reported_by=self.doctor_user,
            released_by=self.doctor_user,
        )
        self.order.status = 'RELEASED'
        self.order.save(update_fields=['status'])

        history_response = self.client.get(f"{reverse('radiology:history')}?patient_id={self.patient_profile.id}")

        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(len(history_response.data), 1)
        self.assertEqual(history_response.data[0]['id'], self.order.id)

        patient_response = self.client.get(f"{reverse('radiology:history')}?patient_id={self.other_patient_profile.id}")
        self.assertEqual(patient_response.status_code, 200)
        self.assertEqual(len(patient_response.data), 0)
