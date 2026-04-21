"""
Simple Dummy Data Seeding Script
Populates database with minimal test data for all modules
Run with: python seed_test_data.py
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
from clinical.models import Doctor, Specialization
from rooms.models import Room, RoomBed
from appointments.models import Appointment, TriageAssessment
from lab.models import TestTemplate, TestField, TestBooking, TestResult, TestResultItem, QCLog
from pharmacy.models import MedicationInventory
from prescriptions.models import Prescription, PrescriptionItem
from inpatient.models import InpatientStay, ProgressNote, DailyRound, DischargePackage

print("\n" + "="*70)
print("SEEDING TEST DATA")
print("="*70 + "\n")

# Get test users
try:
    doctor_user = User.objects.get(email='doctor@hms.test')
    nurse_user = User.objects.get(email='nurse@hms.test')
    lab_tech_user = User.objects.get(email='lab_tech@hms.test')
    patient_user = User.objects.get(email='patient@hms.test')
    admin_user = User.objects.get(email='admin@hms.test')
    print("✅ Test users found\n")
except User.DoesNotExist:
    print("❌ Test users not found. Run seed_users.py first!\n")
    sys.exit(1)

# 1. Create Lab Test Templates
print("Creating lab test templates...")
tests = [
    ('Blood Sugar', 'Fasting blood sugar test', 250),
    ('CBC', 'Complete Blood Count', 300),
    ('Thyroid Profile', 'TSH, T3, T4', 500),
    ('Lipid Profile', 'Cholesterol', 400),
    ('Liver Function', 'AST, ALT, Bilirubin', 350),
]

for name, desc, price in tests:
    template, created = TestTemplate.objects.get_or_create(
        name=name,
        defaults={'description': desc, 'price': price, 'duration_minutes': 30, 'is_available': True}
    )
    if created:
        # Add test fields
        for i in range(2):
            TestField.objects.create(
                template=template,
                field_name=f"Test Parameter {i+1}",
                unit='mg/dL',
                normal_min=50.0,
                normal_max=200.0,
            )

print(f"  ✅ Created {TestTemplate.objects.count()} test templates\n")

# 2. Create QC Logs
print("Creating QC logs...")
templates = TestTemplate.objects.all()
for i in range(5):
    QCLog.objects.get_or_create(
        test_template=random.choice(templates),
        performed_at=timezone.now() - timedelta(days=random.randint(0, 7)),
        defaults={
            'performed_by': lab_tech_user,
            'qc_type': random.choice(['CALIBRATION', 'QUALITY_CONTROL']),
            'result': 'PASSED',
            'details': 'Equipment QC passed',
            'reference_value': '100',
            'actual_value': '100',
        }
    )
print(f"  ✅ Created {QCLog.objects.count()} QC logs\n")

# 3. Create Test Bookings
print("Creating test bookings...")
patient_profiles = PatientProfile.objects.all()[:3]
if patient_profiles:
    for patient in patient_profiles:
        for template in templates[:2]:
            booking, created = TestBooking.objects.get_or_create(
                patient=patient,
                template=template,
                date=timezone.now().date() - timedelta(days=random.randint(0, 10)),
                defaults={
                    'status': 'COMPLETED',
                    'payment_status': 'PAID',
                    'amount': template.price,
                }
            )
            
            if created and booking.status == 'COMPLETED':
                # Create result
                result, _ = TestResult.objects.get_or_create(
                    booking=booking,
                    defaults={
                        'filled_by': lab_tech_user,
                        'is_released': True,
                        'filled_at': timezone.now(),
                    }
                )
                
                # Add result items
                for test_field in template.fields.all()[:2]:
                    TestResultItem.objects.get_or_create(
                        result=result,
                        field=test_field,
                        defaults={
                            'value': f"{random.uniform(float(test_field.normal_min), float(test_field.normal_max)):.1f}",
                            'is_critical': False,
                        }
                    )

print(f"  ✅ Created {TestBooking.objects.count()} test bookings\n")

# 4. Create Medications
print("Creating medications...")
meds = [
    ('Paracetamol 500mg', 'TABLET', 50.0),
    ('Amoxicillin 500mg', 'CAPSULE', 150.0),
    ('Metformin 500mg', 'TABLET', 200.0),
    ('Lisinopril 10mg', 'TABLET', 250.0),
    ('Omeprazole 20mg', 'CAPSULE', 180.0),
]

for med_name, form, price in meds:
    MedicationInventory.objects.get_or_create(
        medication_name=med_name,
        defaults={
            'form': form,
            'unit_price': price,
            'available_quantity': random.randint(100, 500),
            'minimum_threshold': 50,
        }
    )

print(f"  ✅ Created {MedicationInventory.objects.count()} medications\n")

# 5. Create Appointments
print("Creating appointments...")
patient_profiles = PatientProfile.objects.all()[:3]
doctors = Doctor.objects.all()

if patient_profiles and doctors:
    for patient in patient_profiles:
        for i in range(2):
            appointment, created = Appointment.objects.get_or_create(
                patient=patient,
                doctor=random.choice(doctors),
                date=timezone.now().date() + timedelta(days=random.randint(0, 30)),
                start_time='10:00',
                defaults={
                    'status': 'COMPLETED' if i == 0 else 'SCHEDULED',
                    'mode': 'IN_PERSON',
                    'notes': 'General consultation',
                }
            )
            
            if created and appointment.status == 'COMPLETED':
                # Add triage
                TriageAssessment.objects.get_or_create(
                    appointment=appointment,
                    defaults={
                        'vitals_recorded': True,
                        'chief_complaint': 'General checkup',
                        'temperature': 37.0,
                        'systolic': 120,
                        'diastolic': 80,
                        'pulse': 72,
                        'respiratory_rate': 16,
                        'recorded_by': nurse_user,
                    }
                )

print(f"  ✅ Created {Appointment.objects.count()} appointments\n")

# 6. Create Rooms and Beds
print("Creating rooms...")
for floor in ['1', '2', '3']:
    for room_num in range(1, 4):
        room, created = Room.objects.get_or_create(
            room_number=f"{floor}{room_num:02d}",
            defaults={
                'room_type': 'GENERAL',
                'floor': floor,
                'capacity': 2,
                'is_active': True,
            }
        )
        
        if created:
            for bed_letter in ['A', 'B']:
                RoomBed.objects.get_or_create(
                    room=room,
                    bed_number=bed_letter,
                    defaults={'status': 'AVAILABLE'}
                )

print(f"  ✅ Created {Room.objects.count()} rooms\n")

# 7. Create IPD Stays
print("Creating inpatient stays...")
patient_profiles = PatientProfile.objects.all()[:2]
doctors_list = Doctor.objects.all()
rooms_list = Room.objects.all()

if patient_profiles and doctors_list:
    for idx, patient in enumerate(patient_profiles):
        admission_date = timezone.now() - timedelta(days=random.randint(1, 10))
        
        stay, created = InpatientStay.objects.get_or_create(
            patient=patient,
            admission_date=admission_date,
            defaults={
                'attending_doctor': random.choice(doctors_list),
                'admitted_by': admin_user,
                'primary_diagnosis': 'Pneumonia',
                'admission_reason': 'Fever and cough',
                'care_notes': 'Patient admitted for treatment',
                'status': 'ADMITTED' if idx == 0 else 'DISCHARGED',
                'actual_discharge_date': admission_date + timedelta(days=5) if idx > 0 else None,
            }
        )
        
        if created:
            # Add progress notes
            for i in range(2):
                ProgressNote.objects.create(
                    inpatient_stay=stay,
                    author=random.choice([doctor_user, nurse_user]),
                    note_type='PROGRESS',
                    clinical_findings='Patient stable',
                    assessment='Improving',
                    plan='Continue treatment',
                )
            
            # Add rounds
            DailyRound.objects.create(
                inpatient_stay=stay,
                round_date=admission_date.date(),
                round_assessor=doctor_user,
                round_notes='Patient doing well',
                vital_assessment='Stable',
                current_status='Improving',
                is_signed=True,
                signed_by=doctor_user,
                signed_at=timezone.now(),
            )
            
            # Add discharge package if discharged
            if stay.status == 'DISCHARGED':
                DischargePackage.objects.create(
                    inpatient_stay=stay,
                    discharge_summary='Patient recovered',
                    discharge_diagnoses='Pneumonia - treated',
                    discharge_instructions='Rest and take medications',
                    follow_up_date=stay.actual_discharge_date + timedelta(days=7),
                    follow_up_provider='Dr. John Smith',
                    follow_up_specialty='General Medicine',
                    nursing_clearance=True,
                    pharmacy_clearance=True,
                    billing_clearance=True,
                    final_approved=True,
                    doctor_signed_off_by=doctor_user,
                    doctor_signed_off_at=timezone.now(),
                )

print(f"  ✅ Created {InpatientStay.objects.count()} IPD stays\n")

# 8. Create Prescriptions
print("Creating prescriptions...")
appointments = Appointment.objects.filter(status='COMPLETED')[:3]

for appointment in appointments:
    if not hasattr(appointment, 'prescription'):
        prescription, created = Prescription.objects.get_or_create(
            appointment=appointment,
            defaults={
                'doctor': appointment.doctor,
                'patient': appointment.patient,
                'notes': 'Follow up in 2 weeks',
                'advice': 'Take medications regularly',
                'follow_up_date': timezone.now().date() + timedelta(days=14),
                'refill_status': 'ACTIVE',
            }
        )
        
        if created:
            # Add prescription items
            medications = MedicationInventory.objects.all()
            for med in medications[:2]:
                PrescriptionItem.objects.create(
                    prescription=prescription,
                    medication_name=med.medication_name,
                    dosage='500mg',
                    frequency='BD',
                    duration_days=7,
                    quantity=14,
                    instructions='Take with food',
                )

print(f"  ✅ Created {Prescription.objects.count()} prescriptions\n")

print("="*70)
print("✅ TEST DATA SEEDING COMPLETED!")
print("="*70)
print("\nData Summary:")
print(f"  • Test Templates: {TestTemplate.objects.count()}")
print(f"  • Test Bookings: {TestBooking.objects.count()}")
print(f"  • QC Logs: {QCLog.objects.count()}")
print(f"  • Medications: {MedicationInventory.objects.count()}")
print(f"  • Appointments: {Appointment.objects.count()}")
print(f"  • Rooms: {Room.objects.count()}")
print(f"  • IPD Stays: {InpatientStay.objects.count()}")
print(f"  • Prescriptions: {Prescription.objects.count()}")
print("\n🎉 All pages now have data to display!\n")
print("="*70 + "\n")
