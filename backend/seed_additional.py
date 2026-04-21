"""
Additional Dummy Data for Appointments and Prescriptions
Run with: python seed_additional.py
"""
import os
import sys
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from django.utils import timezone
from users.models import User, PatientProfile
from clinical.models import Doctor
from appointments.models import Appointment, TriageAssessment
from prescriptions.models import Prescription, PrescriptionItem
from pharmacy.models import MedicationInventory

print("\n" + "="*70)
print("SEEDING ADDITIONAL DATA (Appointments & Prescriptions)")
print("="*70 + "\n")

# Get test users
try:
    doctor_user = User.objects.get(email='doctor@hms.test')
    nurse_user = User.objects.get(email='nurse@hms.test')
    admin_user = User.objects.get(email='admin@hms.test')
    print("✅ Test users found\n")
except User.DoesNotExist:
    print("❌ Test users not found. Run seed_users.py first!\n")
    sys.exit(1)

# 1. Create Appointments
print("Creating appointments...")
patient_profiles = PatientProfile.objects.all()[:5]
doctors_list = Doctor.objects.all()

if patient_profiles and doctors_list:
    for patient in patient_profiles:
        try:
            # Create 1-2 appointments per patient
            for i in range(random.randint(1, 2)):
                appt_date = timezone.now().date() + timedelta(days=random.randint(-5, 30))
                
                appointment, created = Appointment.objects.get_or_create(
                    patient=patient,
                    doctor=random.choice(doctors_list),
                    date=appt_date,
                    start_time=f"{random.choice([9, 10, 11, 14, 15, 16])}:00",
                    defaults={
                        'status': 'SCHEDULED' if appt_date > timezone.now().date() else 'COMPLETED',
                        'mode': random.choice(['IN_PERSON', 'TELE']),
                        'notes': f'Follow-up appointment',
                    }
                )
                
                # Add triage for completed appointments
                if created and appointment.status == 'COMPLETED':
                    try:
                        TriageAssessment.objects.get_or_create(
                            appointment=appointment,
                            defaults={
                                'vitals_recorded': True,
                                'chief_complaint': f'Check-up',
                                'temperature': round(36.5 + random.uniform(-0.5, 1.0), 1),
                                'systolic': random.randint(110, 130),
                                'diastolic': random.randint(70, 90),
                                'pulse': random.randint(60, 100),
                                'respiratory_rate': random.randint(14, 20),
                                'recorded_by': nurse_user,
                            }
                        )
                    except Exception as e:
                        pass
        except Exception as e:
            print(f"  ⚠️  Appointment creation issue: {e}")

print(f"  ✅ Created {Appointment.objects.count()} appointments\n")

# 2. Create Prescriptions
print("Creating prescriptions...")
completed_appointments = Appointment.objects.filter(status='COMPLETED')[:5]
medications = MedicationInventory.objects.all()

if completed_appointments and medications:
    for appointment in completed_appointments:
        try:
            if not Prescription.objects.filter(appointment=appointment).exists():
                prescription = Prescription.objects.create(
                    appointment=appointment,
                    doctor=appointment.doctor,
                    patient=appointment.patient,
                    notes='Take medications as prescribed',
                    advice='Take with food, avoid alcohol',
                    follow_up_date=timezone.now().date() + timedelta(days=14),
                    refill_status='ACTIVE',
                )
                
                # Add prescription items
                for _ in range(random.randint(1, 3)):
                    med = random.choice(medications)
                    PrescriptionItem.objects.create(
                        prescription=prescription,
                        medication_name=med.medication_name,
                        dosage=f'{random.choice([250, 500, 1000])}mg',
                        frequency=random.choice(['OD', 'BD', 'TDS', 'QID']),
                        duration_days=random.randint(5, 14),
                        quantity=random.randint(5, 30),
                        instructions='Take with food',
                    )
        except Exception as e:
            print(f"  ⚠️  Prescription creation issue: {e}")

print(f"  ✅ Created {Prescription.objects.count()} prescriptions\n")

print("="*70)
print("✅ ADDITIONAL DATA SEEDING COMPLETED!")
print("="*70)
print("\nData Summary:")
print(f"  • Appointments: {Appointment.objects.count()}")
print(f"  • Prescriptions: {Prescription.objects.count()}")
print(f"  • Total PrescriptionItems: {Prescription.objects.aggregate(count=__import__('django.db.models', fromlist=['Sum']).Sum('items__id'))}")
print("\n🎉 More data added!\n")
print("="*70 + "\n")
