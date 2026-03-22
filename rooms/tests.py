from django.test import TestCase
from django.urls import reverse

from clinical.models import Doctor
from rooms.models import AdmissionRequest, Room, RoomAssignment, RoomBed
from users.models import PatientProfile, User


class RoomsWorkflowTests(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            email='patient@example.com',
            username='patient1',
            password='pass1234',
            role='PATIENT',
            is_active=True,
        )
        self.patient_profile, _ = PatientProfile.objects.get_or_create(
            user=self.patient_user,
            defaults={'full_name': 'Patient One'},
        )

        self.doctor_user = User.objects.create_user(
            email='doctor@example.com',
            username='doctor1',
            password='pass1234',
            role='DOCTOR',
            is_active=True,
        )
        self.doctor_profile = Doctor.objects.create(user=self.doctor_user)

        self.receptionist_user = User.objects.create_user(
            email='reception@example.com',
            username='reception1',
            password='pass1234',
            role='RECEPTIONIST',
            is_active=True,
        )

        self.room = Room.objects.create(
            room_number='R101',
            room_type='GENERAL',
            floor='1',
            capacity=1,
            is_active=True,
        )
        self.bed = RoomBed.objects.create(room=self.room, bed_number='1', status='AVAILABLE')

    def test_patient_booking_creates_pending_request_not_assignment(self):
        self.client.force_login(self.patient_user)

        response = self.client.post(
            reverse('rooms:patient_book_room'),
            {'room_id': self.room.id},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(RoomAssignment.objects.count(), 0)
        self.assertEqual(AdmissionRequest.objects.count(), 1)

        req = AdmissionRequest.objects.first()
        self.assertEqual(req.status, 'PENDING')
        self.assertEqual(req.patient, self.patient_profile)
        self.assertEqual(req.preferred_room, self.room)

    def test_receptionist_cannot_assign_occupied_bed(self):
        self.bed.status = 'OCCUPIED'
        self.bed.save(update_fields=['status'])

        self.client.force_login(self.receptionist_user)
        response = self.client.post(
            reverse('rooms:receptionist_assign_room'),
            {
                'patient_id': self.patient_profile.id,
                'room_id': self.room.id,
                'bed_id': self.bed.id,
                'doctor_id': self.doctor_profile.id,
                'admission_notes': 'Needs close monitoring',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(RoomAssignment.objects.count(), 0)

    def test_reject_admission_request_is_post_only(self):
        self.client.force_login(self.receptionist_user)
        admission_request = AdmissionRequest.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            requested_by=self.doctor_user,
            reason='Inpatient observation required',
            status='PENDING',
        )

        response = self.client.get(
            reverse('rooms:receptionist_reject_admission_request', args=[admission_request.id])
        )

        self.assertEqual(response.status_code, 405)
