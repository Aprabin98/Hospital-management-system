from datetime import date, time, timedelta

from django.core.management.base import BaseCommand

from appointments.models import Appointment
from clinical.models import Doctor, PatientVisit, Specialization
from clinical.patient_ai import analyze_patient_visit
from lab.models import TestSchedule, TestTemplate
from users.models import PatientAllergy, PatientHealthRecord, PatientProfile, User


class Command(BaseCommand):
    help = 'Create demo data for AI-assisted patient management defence flow.'

    def handle(self, *args, **options):
        password = 'Demo@12345'
        doctor_user, _ = User.objects.get_or_create(
            email='demo.doctor@hms.test',
            defaults={
                'username': 'demo_doctor',
                'first_name': 'Demo',
                'last_name': 'Doctor',
                'role': 'DOCTOR',
                'is_active': True,
            },
        )
        doctor_user.set_password(password)
        doctor_user.save()

        patient_user, _ = User.objects.get_or_create(
            email='demo.patient@hms.test',
            defaults={
                'username': 'demo_patient',
                'first_name': 'Sita',
                'last_name': 'Shrestha',
                'role': 'PATIENT',
                'is_active': True,
            },
        )
        patient_user.set_password(password)
        patient_user.save()

        specialization, _ = Specialization.objects.get_or_create(name='General Medicine')
        doctor, _ = Doctor.objects.get_or_create(
            user=doctor_user,
            defaults={'specialization': specialization, 'consultation_fee': 500, 'is_available': True},
        )

        patient, _ = PatientProfile.objects.get_or_create(
            user=patient_user,
            defaults={'full_name': 'Sita Shrestha', 'phone': '9800000000', 'blood_group': 'A+', 'emergency_contact': '9811111111'},
        )
        PatientAllergy.objects.get_or_create(patient=patient, allergen='Penicillin', defaults={'severity': 'SEVERE'})
        PatientHealthRecord.objects.update_or_create(
            patient=patient,
            defaults={
                'allergies': 'Penicillin',
                'chronic_conditions': 'Diabetes\nHypertension',
                'current_medications': 'Metformin\nAmlodipine',
                'family_history': 'Family history of diabetes',
                'updated_by': doctor_user,
            },
        )

        for name, price in [('CBC', 500), ('CRP', 700), ('Chest X-Ray', 1200)]:
            template, _ = TestTemplate.objects.get_or_create(
                name=name,
                defaults={'price': price, 'duration_minutes': 30, 'is_available': True},
            )
            for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
                TestSchedule.objects.update_or_create(
                    template=template,
                    day=day,
                    defaults={'start_time': time(9, 0), 'end_time': time(17, 0), 'max_bookings': 20, 'is_active': True},
                )

        old_visit, _ = PatientVisit.objects.get_or_create(
            patient=patient,
            symptoms='fever and cough last month',
            defaults={
                'doctor': doctor,
                'diagnosis': 'Viral fever',
                'doctor_notes': 'Recovered with supportive care.',
                'prescribed_medicines': 'Paracetamol',
                'follow_up_completed': True,
                'created_by': doctor_user,
            },
        )
        if not old_visit.ai_summary:
            ai = analyze_patient_visit(patient, old_visit.symptoms, old_visit.prescribed_medicines)
            old_visit.ai_possible_causes = '\n'.join(ai['possible_causes'])
            old_visit.ai_recommended_tests = '\n'.join(ai['recommended_tests'])
            old_visit.ai_risk_level = ai['risk_level']
            old_visit.ai_red_flags = '\n'.join(ai['red_flags'])
            old_visit.ai_summary = ai['summary']
            old_visit.save()

        appointment, _ = Appointment.objects.get_or_create(
            patient=patient,
            doctor=doctor,
            date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            defaults={'end_time': time(10, 30), 'status': 'CONFIRMED', 'notes': 'Demo defence appointment'},
        )

        self.stdout.write(self.style.SUCCESS('Demo ready'))
        self.stdout.write(f'Doctor login: demo.doctor@hms.test / {password}')
        self.stdout.write(f'Patient id: {patient.id}')
        self.stdout.write(f'Appointment id: {appointment.id}')
