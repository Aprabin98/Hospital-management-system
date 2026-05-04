"""
Ultra-simple Dummy Data Seeding Script
Populates database with minimal test data for remaining core modules
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
from clinical.models import Doctor, Specialization
from lab.models import TestTemplate, TestField
from appointments.models import Appointment
from prescriptions.models import Prescription

print("\n" + "="*70)
print("SEEDING SIMPLE TEST DATA (Phase 3 - Simplified)")
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

# 2. Create Appointments
print("Creating sample appointments...")
patient_profiles = PatientProfile.objects.all()[:2]
doctors_list = Doctor.objects.all()

if patient_profiles and doctors_list:
    for idx, patient in enumerate(patient_profiles):
        try:
            appointment_date = timezone.now().date() + timedelta(days=random.randint(1, 30))
            Appointment.objects.get_or_create(
                patient=patient,
                doctor=doctors_list[idx % len(doctors_list)],
                date=appointment_date,
                defaults={
                    'time_slot': '10:00',
                    'reason': 'Regular checkup',
                    'status': 'CONFIRMED',
                    'is_online': False,
                }
            )
        except Exception as e:
            print(f"  ⚠️  Appointment creation issue: {e}")

print(f"  ✅ Created {Appointment.objects.count()} sample appointments\n")

print("="*70)
print("✅ SIMPLIFIED TEST DATA SEEDING COMPLETED!")
print("="*70)
print("\nData Summary:")
print(f"  • Test Templates: {TestTemplate.objects.count()}")
print(f"  • Appointments: {Appointment.objects.count()}")
print(f"  • Rooms: {Room.objects.count()}")
print(f"  • IPD Stays: {InpatientStay.objects.count()}")
print("\n🎉 Database populated with test data!\n")
print("="*70 + "\n")
