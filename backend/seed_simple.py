"""
Ultra-simple Dummy Data Seeding Script
Populates database with minimal test data for all modules
Run with: python seed_simple.py
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
from rooms.models import Room, RoomBed
from lab.models import TestTemplate, TestField, QCLog
from pharmacy.models import MedicationInventory
from inpatient.models import InpatientStay, ProgressNote, DailyRound, DischargePackage

print("\n" + "="*70)
print("SEEDING SIMPLE TEST DATA")
print("="*70 + "\n")

# Get test users
try:
    doctor_user = User.objects.get(email='doctor@hms.test')
    nurse_user = User.objects.get(email='nurse@hms.test')
    lab_tech_user = User.objects.get(email='lab_tech@hms.test')
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
]

for name, desc, price in tests:
    template, created = TestTemplate.objects.get_or_create(
        name=name,
        defaults={'description': desc, 'price': price, 'duration_minutes': 30, 'is_available': True}
    )
    if created:
        # Add test fields
        for i in range(1):
            TestField.objects.get_or_create(
                template=template,
                field_name=f"Result {i+1}",
                defaults={
                    'unit': 'mg/dL',
                    'normal_min': 50.0,
                    'normal_max': 200.0,
                }
            )

print(f"  ✅ Created {TestTemplate.objects.count()} test templates\n")

# 2. Create QC Logs
print("Creating QC logs...")
templates = TestTemplate.objects.all()
if templates:
    for i in range(3):
        try:
            QCLog.objects.get_or_create(
                test_template=templates[i % len(templates)],
                performed_at=timezone.now() - timedelta(days=i),
                defaults={
                    'performed_by': lab_tech_user,
                    'qc_type': 'CALIBRATION',
                    'result': 'PASSED',
                    'details': 'Equipment QC passed',
                    'reference_value': '100',
                    'actual_value': f'{100 + random.randint(-5, 5)}',
                }
            )
        except Exception as e:
            print(f"  ⚠️  QC log creation issue: {e}")

print(f"  ✅ Created {QCLog.objects.count()} QC logs\n")

# 3. Create Medications
print("Creating medications...")
meds = [
    ('Paracetamol 500mg', 'TABLET', 50.0),
    ('Amoxicillin 500mg', 'CAPSULE', 150.0),
    ('Metformin 500mg', 'TABLET', 200.0),
]

today = timezone.now().date()
for med_name, unit, cost in meds:
    MedicationInventory.objects.get_or_create(
        medication_name=med_name,
        batch_number=f"BATCH{random.randint(1000, 9999)}",
        manufacturer='Test Pharma Ltd',
        defaults={
            'unit': unit,
            'unit_cost': cost,
            'quantity': random.randint(100, 500),
            'manufacture_date': today - timedelta(days=90),
            'expiry_date': today + timedelta(days=365),
            'received_by': admin_user,
        }
    )

print(f"  ✅ Created {MedicationInventory.objects.count()} medications\n")

# 4. Create Rooms
print("Creating rooms...")
for floor in ['1', '2']:
    for room_num in range(1, 3):
        try:
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
        except Exception as e:
            print(f"  ⚠️  Room creation issue: {e}")

print(f"  ✅ Created {Room.objects.count()} rooms\n")

# 5. Create IPD Stays
print("Creating inpatient stays...")
patient_profiles = PatientProfile.objects.all()[:2]
doctors_list = Doctor.objects.all()

if patient_profiles and doctors_list:
    for idx, patient in enumerate(patient_profiles):
        try:
            admission_datetime = timezone.now() - timedelta(days=random.randint(1, 10))
            
            stay, created = InpatientStay.objects.get_or_create(
                patient=patient,
                admission_datetime=admission_datetime,
                defaults={
                    'attending_doctor': doctors_list[idx % len(doctors_list)],
                    'admitted_by': admin_user,
                    'primary_diagnosis': 'General Condition',
                    'admission_reason': 'Medical examination',
                    'care_notes': 'Patient admitted',
                    'status': 'ADMITTED',
                }
            )
            
            if created:
                # Add progress notes
                ProgressNote.objects.create(
                    inpatient_stay=stay,
                    author=doctor_user,
                    note_type='PROGRESS',
                    clinical_findings='Patient stable',
                    assessment='Improving',
                    plan='Continue treatment',
                )
                
                # Add rounds
                DailyRound.objects.create(
                    inpatient_stay=stay,
                    round_date=admission_datetime.date(),
                    round_assessor=doctor_user,
                    round_notes='Patient doing well',
                    vital_assessment='Stable',
                    current_status='Improving',
                    is_signed=True,
                    signed_by=doctor_user,
                    signed_at=timezone.now(),
                )
        except Exception as e:
            print(f"  ⚠️  IPD stay creation issue: {e}")

print(f"  ✅ Created {InpatientStay.objects.count()} IPD stays\n")

print("="*70)
print("✅ TEST DATA SEEDING COMPLETED!")
print("="*70)
print("\nData Summary:")
print(f"  • Test Templates: {TestTemplate.objects.count()}")
print(f"  • QC Logs: {QCLog.objects.count()}")
print(f"  • Medications: {MedicationInventory.objects.count()}")
print(f"  • Rooms: {Room.objects.count()}")
print(f"  • IPD Stays: {InpatientStay.objects.count()}")
print("\n🎉 Database populated with test data!\n")
print("="*70 + "\n")
