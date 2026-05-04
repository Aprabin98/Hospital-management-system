"""
Comprehensive Dummy Data Seeding Script
Populates the database with realistic test data for all modules
Run with: python seed_dummy_data.py
"""
import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from django.utils import timezone
from users.models import User, PatientProfile
from clinical.models import Doctor, Specialization, DoctorSchedule, Shift
from appointments.models import Appointment, TriageAssessment, Queue
from lab.models import TestTemplate, TestField, TestBooking, TestResult, TestResultItem, LabSample
from prescriptions.models import Prescription, PrescriptionItem
from payments.models import Payment

# Test users
USERS = {
    'admin': User.objects.get(email='admin@hms.test'),
    'doctor': User.objects.get(email='doctor@hms.test'),
    'nurse': User.objects.get(email='nurse@hms.test'),
    'lab_tech': User.objects.get(email='lab_tech@hms.test'),
    'pharmacist': User.objects.get(email='pharmacist@hms.test'),
    'receptionist': User.objects.get(email='receptionist@hms.test'),
    'patient': User.objects.get(email='patient@hms.test'),
    'patient2': User.objects.get(email='patient2@hms.test'),
}

DIAGNOSES = [
    'Hypertension', 'Diabetes Mellitus Type 2', 'Pneumonia', 'Gastritis',
    'Fever', 'Cough', 'Headache', 'Anxiety', 'Asthma', 'COPD',
    'Acute Bronchitis', 'Migraine', 'Hyperlipidemia', 'Obesity', 'Anemia'
]

SYMPTOMS = [
    'Fever', 'Cough', 'Chest pain', 'Shortness of breath', 'Nausea',
    'Vomiting', 'Diarrhea', 'Abdominal pain', 'Headache', 'Dizziness',
    'Fatigue', 'Chills', 'Sore throat', 'Congestion'
]

MEDICATIONS = [
    ('Paracetamol', '500mg', 50.0),
    ('Amoxicillin', '500mg', 150.0),
    ('Metformin', '500mg', 200.0),
    ('Atorvastatin', '20mg', 300.0),
    ('Lisinopril', '10mg', 250.0),
    ('Omeprazole', '20mg', 180.0),
    ('Aspirin', '100mg', 120.0),
    ('Ibuprofen', '400mg', 100.0),
    ('Loratadine', '10mg', 80.0),
    ('Ciprofloxacin', '500mg', 350.0),
]

TEST_TEMPLATES = [
    ('Blood Sugar', 'Fasting blood sugar test', 'Fast for 8 hours', 250.0),
    ('CBC', 'Complete Blood Count', None, 300.0),
    ('Thyroid Profile', 'TSH, T3, T4 levels', None, 500.0),
    ('Lipid Profile', 'Cholesterol levels', 'Fasting preferred', 400.0),
    ('Kidney Function', 'Creatinine, BUN', None, 350.0),
    ('Liver Function', 'AST, ALT, Bilirubin', None, 350.0),
    ('Urinalysis', 'Complete urine test', None, 150.0),
    ('COVID-19 RT-PCR', 'COVID-19 testing', None, 800.0),
]

print("\n" + "="*70)
print("SEEDING COMPREHENSIVE DUMMY DATA")
print("="*70 + "\n")

def create_additional_patients():
    """Create additional patient profiles"""
    print("Creating additional patients...")
    patient_names = [
        ('John Doe', 'M', '1975-05-15'),
        ('Jane Smith', 'F', '1982-07-20'),
        ('Michael Johnson', 'M', '1990-01-10'),
        ('Sarah Williams', 'F', '1988-03-25'),
        ('Robert Brown', 'M', '1970-09-05'),
        ('Emily Davis', 'F', '1995-11-12'),
        ('David Miller', 'M', '1978-02-18'),
        ('Lisa Anderson', 'F', '1985-06-30'),
    ]
    
    for idx, (name, gender, dob_str) in enumerate(patient_names):
        email = f"patient{idx+3}@hms.test"
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': name.split()[0],
                'last_name': name.split()[1] if len(name.split()) > 1 else '',
                'role': 'PATIENT',
            }
        )
        
        if created:
            user.set_password('Patient@123456')
            user.save()
            PatientProfile.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': name,
                    'date_of_birth': datetime.strptime(dob_str, '%Y-%m-%d').date(),
                    'gender': gender,
                    'phone': f'+1-555-{1000+idx:04d}',
                    'blood_group': random.choice(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']),
                }
            )
            print(f"  ✅ Created patient: {name}")

def create_specializations():
    """Create doctor specializations"""
    print("\nCreating specializations...")
    specs = ['General Medicine', 'Cardiology', 'Orthopedics', 'Neurology', 'Oncology', 'Pediatrics']
    for spec in specs:
        Specialization.objects.get_or_create(name=spec)
    print(f"  ✅ Created {len(specs)} specializations")

def create_additional_doctors():
    """Create additional doctor profiles"""
    print("\nCreating additional doctors...")
    doctor_data = [
        ('Dr. Sarah Johnson', 'Cardiology', 'sarah.johnson@hms.test'),
        ('Dr. Michael Brown', 'Orthopedics', 'michael.brown@hms.test'),
        ('Dr. Emily Davis', 'Neurology', 'emily.davis@hms.test'),
    ]
    
    for name, spec, email in doctor_data:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': name.split()[1],
                'last_name': name.split()[2] if len(name.split()) > 2 else '',
                'role': 'DOCTOR',
                'is_staff': True,
            }
        )
        
        if created:
            user.set_password('Doctor@123456')
            user.save()
        
        specialization = Specialization.objects.get(name=spec)
        doctor, created = Doctor.objects.get_or_create(
            user=user,
            defaults={
                'specialization': specialization,
                'consultation_fee': random.randint(300, 800),
                'experience_years': random.randint(5, 25),
                'is_available': True,
            }
        )
        
        if created:
            print(f"  ✅ Created doctor: {name} ({spec})")

def create_rooms_and_beds():
    """Create rooms and beds"""
    print("\nCreating rooms and beds...")
    floors = ['1', '2', '3', '4', '5']
    room_types = ['GENERAL', 'SEMI_PRIVATE', 'PRIVATE', 'ICU']
    
    room_count = 0
    for floor in floors:
        for room_num in range(1, 6):
            room_number = f"{floor}{room_num:02d}"
            room_type = random.choice(room_types)
            capacity = 1 if room_type == 'PRIVATE' else 2 if room_type == 'SEMI_PRIVATE' else 4
            
            room, created = Room.objects.get_or_create(
                room_number=room_number,
                defaults={
                    'room_type': room_type,
                    'floor': floor,
                    'capacity': capacity,
                    'is_active': True,
                }
            )
            
            if created:
                for bed_num in range(1, capacity + 1):
                    RoomBed.objects.get_or_create(
                        room=room,
                        bed_number=chr(64 + bed_num),  # A, B, C, D
                        defaults={'status': 'AVAILABLE'}
                    )
                room_count += 1
    
    print(f"  ✅ Created {room_count} rooms with beds")

def create_shifts():
    """Create doctor shifts"""
    print("\nCreating shifts...")
    shifts = [
        ('Morning', '08:00', '16:00'),
        ('Afternoon', '14:00', '22:00'),
        ('Night', '22:00', '08:00'),
    ]
    
    for name, start, end in shifts:
        Shift.objects.get_or_create(
            name=name,
            defaults={
                'start_time': start,
                'end_time': end,
            }
        )
    print(f"  ✅ Created {len(shifts)} shifts")

def create_doctor_schedules():
    """Create doctor schedules"""
    print("\nCreating doctor schedules...")
    doctors = Doctor.objects.all()[:3]
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
    shifts = Shift.objects.all()
    
    schedule_count = 0
    for doctor in doctors:
        for day in days:
            for shift in shifts[:1]:  # Morning shift only
                DoctorSchedule.objects.get_or_create(
                    doctor=doctor,
                    day=day,
                    shift=shift,
                )
                schedule_count += 1
    
    print(f"  ✅ Created {schedule_count} doctor schedules")

def create_appointments():
    """Create appointments"""
    print("\nCreating appointments...")
    patients = PatientProfile.objects.all()[:5]
    doctors = Doctor.objects.all()
    statuses = ['SCHEDULED', 'COMPLETED', 'CANCELLED']
    
    appointment_count = 0
    for idx, patient in enumerate(patients):
        for i in range(2):
            doctor = doctors[idx % len(doctors)]
            appointment_date = timezone.now() + timedelta(days=random.randint(-30, 30))
            
            appointment, created = Appointment.objects.get_or_create(
                patient=patient,
                appointment_date=appointment_date,
                reason_for_visit=random.choice(DIAGNOSES),
                defaults={
                    'doctor': doctor,
                    'status': random.choice(statuses),
                    'mode': random.choice(['IN_PERSON', 'TELEMEDICINE']),
                    'created_at': appointment_date - timedelta(days=5),
                }
            )
            
            if created:
                appointment_count += 1
                
                # Create triage assessment if appointment exists
                TriageAssessment.objects.get_or_create(
                    appointment=appointment,
                    defaults={
                        'vitals_recorded': True,
                        'chief_complaint': random.choice(SYMPTOMS),
                        'temperature': round(36.5 + random.uniform(-1, 2), 1),
                        'systolic': random.randint(100, 160),
                        'diastolic': random.randint(60, 100),
                        'pulse': random.randint(60, 100),
                        'respiratory_rate': random.randint(14, 20),
                        'recorded_by': USERS['nurse'],
                    }
                )
    
    print(f"  ✅ Created {appointment_count} appointments")

def create_lab_tests():
    """Create lab test templates and bookings"""
    print("\nCreating lab tests...")
    
    # Create test templates
    template_count = 0
    for name, desc, prep, price in TEST_TEMPLATES:
        template, created = TestTemplate.objects.get_or_create(
            name=name,
            defaults={
                'description': desc,
                'preparation': prep or '',
                'price': price,
                'duration_minutes': random.randint(15, 120),
                'is_available': True,
            }
        )
        
        if created:
            template_count += 1
            # Create test fields
            field_count = random.randint(2, 5)
            for j in range(field_count):
                TestField.objects.create(
                    template=template,
                    field_name=f"Test Field {j+1}",
                    unit=random.choice(['mg/dL', 'g/dL', 'mIU/L', '%', 'mg/L', 'cells/μL']),
                    normal_min=random.uniform(50, 100),
                    normal_max=random.uniform(150, 200),
                )
    
    print(f"  ✅ Created {template_count} test templates with fields")
    
    # Create test bookings
    print("  Creating test bookings...")
    patients = PatientProfile.objects.all()[:5]
    templates = TestTemplate.objects.all()
    
    booking_count = 0
    for patient in patients:
        for i in range(3):
            template = random.choice(templates)
            booking_date = timezone.now().date() + timedelta(days=random.randint(-20, 5))
            
            booking, created = TestBooking.objects.get_or_create(
                patient=patient,
                template=template,
                date=booking_date,
                defaults={
                    'status': random.choice(['COMPLETED', 'PENDING', 'CANCELLED']),
                    'payment_status': 'PAID',
                    'amount': template.price,
                    'booked_by': USERS['receptionist'],
                }
            )
            
            if created:
                booking_count += 1
                
                # Create test result if booking is completed
                if booking.status == 'COMPLETED':
                    result, _ = TestResult.objects.get_or_create(
                        booking=booking,
                        defaults={
                            'filled_by': USERS['lab_tech'],
                            'is_released': True,
                            'filled_at': timezone.now(),
                            'notes': 'Test completed successfully',
                        }
                    )
                    
                    # Create result items
                    for field in template.fields.all()[:2]:
                        TestResultItem.objects.get_or_create(
                            result=result,
                            test_field=field,
                            defaults={
                                'value': f"{random.uniform(field.normal_min, field.normal_max):.1f}",
                                'is_critical': random.choice([False, False, True]),  # 33% critical
                            }
                        )
    
    print(f"  ✅ Created {booking_count} test bookings")

def create_qc_logs():
    """Create QC logs"""
    print("\nCreating QC logs...")
    templates = TestTemplate.objects.all()
    
    qc_count = 0
    for i in range(8):
        template = random.choice(templates)
        QCLog.objects.get_or_create(
            qc_type=random.choice(['CALIBRATION', 'QUALITY_CONTROL', 'MAINTENANCE']),
            test_template=template,
            performed_at=timezone.now() - timedelta(days=random.randint(0, 30)),
            defaults={
                'performed_by': USERS['lab_tech'],
                'result': random.choice(['PASSED', 'PASSED', 'PASSED', 'CONDITIONAL']),
                'details': 'Equipment QC check performed',
                'reference_value': '100',
                'actual_value': f"{random.randint(95, 105)}",
                'deviation': f"{random.randint(0, 5)}%",
            }
        )
        qc_count += 1
    
    print(f"  ✅ Created {qc_count} QC logs")

def create_medications():
    """Create medications inventory"""
    print("\nCreating medications...")
    
    med_count = 0
    for name, strength, price in MEDICATIONS:
        med, created = MedicationInventory.objects.get_or_create(
            medication_name=name,
            strength=strength,
            defaults={
                'form': random.choice(['TABLET', 'CAPSULE', 'SYRUP', 'INJECTION']),
                'manufacturer': f"{name} Inc.",
                'unit_price': price,
                'available_quantity': random.randint(100, 1000),
                'minimum_threshold': 50,
            }
        )
        
        if created:
            med_count += 1
    
    print(f"  ✅ Created {med_count} medications")

def create_prescriptions():
    """Create prescriptions"""
    print("\nCreating prescriptions...")
    
    medications = [name for name, _, _ in MEDICATIONS]
    
    prescription_count = 0
    # Get appointments that don't have prescriptions
    appointments = Appointment.objects.filter(prescription__isnull=True)[:5]
    
    for appointment in appointments:
        prescription, created = Prescription.objects.get_or_create(
            appointment=appointment,
            defaults={
                'doctor': appointment.doctor,
                'patient': appointment.patient,
                'notes': random.choice(['Take with meals', 'Avoid dairy', 'Bedtime only']),
                'advice': 'Follow up in 2 weeks',
                'follow_up_date': timezone.now().date() + timedelta(days=14),
                'refill_status': 'ACTIVE',
                'total_refills_allowed': 2,
                'expiry_date': timezone.now().date() + timedelta(days=365),
            }
        )
        
        if created:
            prescription_count += 1
            # Create prescription items
            for _ in range(random.randint(1, 3)):
                medication_name = random.choice(medications)
                PrescriptionItem.objects.create(
                    prescription=prescription,
                    medication_name=medication_name,
                    dosage=random.choice(['100mg', '250mg', '500mg']),
                    frequency=random.choice(['OD', 'BD', 'TDS']),
                    duration_days=random.randint(5, 30),
                    quantity=random.randint(10, 60),
                    instructions=random.choice(['Take with food', 'On empty stomach', 'As needed']),
                )
    
    print(f"  ✅ Created {prescription_count} prescriptions with items")

def create_inpatient_stays():
    """Create inpatient stays"""
    print("\nCreating inpatient stays...")
    patients = PatientProfile.objects.all()[:4]
    doctors = Doctor.objects.all()
    rooms = Room.objects.filter(is_active=True)[:4]
    
    stay_count = 0
    for idx, patient in enumerate(patients):
        # Create admission request first
        admission_req, _ = AdmissionRequest.objects.get_or_create(
            patient=patient,
            requested_date=timezone.now() - timedelta(days=random.randint(5, 30)),
            defaults={
                'requested_by': USERS['doctor'],
                'status': 'APPROVED',
                'approval_date': timezone.now() - timedelta(days=random.randint(1, 28)),
            }
        )
        
        # Get room assignment
        room = rooms[idx % len(rooms)]
        bed = room.beds.first()
        
        room_assign, _ = RoomAssignment.objects.get_or_create(
            bed=bed,
            patient=patient,
            defaults={'status': 'OCCUPIED', 'assigned_date': timezone.now() - timedelta(days=5)}
        )
        
        # Create inpatient stay
        admission_date = timezone.now() - timedelta(days=random.randint(5, 30))
        is_discharged = random.choice([True, True, False])
        discharge_date = admission_date + timedelta(days=random.randint(3, 14)) if is_discharged else None
        
        stay, created = InpatientStay.objects.get_or_create(
            patient=patient,
            admission_date=admission_date,
            defaults={
                'attending_doctor': random.choice(doctors),
                'admission_request': admission_req,
                'room_assignment': room_assign,
                'admission_appointment': Appointment.objects.filter(patient=patient).first(),
                'admitted_by': USERS['receptionist'],
                'primary_diagnosis': random.choice(DIAGNOSES),
                'admission_reason': random.choice(SYMPTOMS),
                'care_notes': 'Patient admitted for treatment',
                'status': 'DISCHARGED' if is_discharged else 'ADMITTED',
                'actual_discharge_date': discharge_date,
            }
        )
        
        if created:
            stay_count += 1
            
            # Create progress notes
            for i in range(2):
                ProgressNote.objects.create(
                    inpatient_stay=stay,
                    author=random.choice([USERS['doctor'], USERS['nurse']]),
                    note_type=random.choice(['PROGRESS', 'ROUND', 'NURSING']),
                    clinical_findings=f"Patient showing signs of improvement",
                    assessment='Stable condition',
                    plan='Continue current treatment',
                    created_at=admission_date + timedelta(days=i+1),
                )
            
            # Create daily rounds
            for i in range(2):
                DailyRound.objects.create(
                    inpatient_stay=stay,
                    round_date=(admission_date + timedelta(days=i+1)).date(),
                    round_assessor=USERS['doctor'],
                    round_notes='Patient progressing well',
                    vital_assessment='Vitals stable',
                    current_status='Improving',
                    is_signed=True,
                    signed_by=USERS['doctor'],
                    signed_at=timezone.now(),
                )
            
            # Create discharge package if discharged
            if is_discharged:
                DischargePackage.objects.create(
                    inpatient_stay=stay,
                    discharge_summary='Patient recovered successfully',
                    discharge_diagnoses='Pneumonia - recovered',
                    discharge_instructions='Rest, follow medications, return if symptoms worsen',
                    follow_up_date=discharge_date + timedelta(days=7) if discharge_date else timezone.now().date(),
                    follow_up_provider='Dr. John Smith',
                    follow_up_specialty='General Medicine',
                    nursing_clearance=True,
                    pharmacy_clearance=True,
                    billing_clearance=True,
                    final_approved=True,
                    doctor_signed_off_by=USERS['doctor'],
                    doctor_signed_off_at=timezone.now(),
                    patient_acknowledged_by=stay.patient.user,
                    patient_acknowledged_at=timezone.now(),
                )
    
    print(f"  ✅ Created {stay_count} inpatient stays with notes and rounds")

# Run all seeding functions
try:
    create_specializations()
    create_additional_patients()
    create_additional_doctors()
    create_rooms_and_beds()
    create_shifts()
    create_appointments()
    create_lab_tests()
    create_qc_logs()
    create_medications()
    create_prescriptions()
    create_inpatient_stays()
    
    print("\n" + "="*70)
    print("✅ DUMMY DATA SEEDING COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nData Summary:")
    print(f"  • Patients: {PatientProfile.objects.count()}")
    print(f"  • Doctors: {Doctor.objects.count()}")
    print(f"  • Appointments: {Appointment.objects.count()}")
    print(f"  • Lab Tests: {TestBooking.objects.count()}")
    print(f"  • Prescriptions: {Prescription.objects.count()}")
    print(f"  • Medications: {MedicationInventory.objects.count()}")
    print(f"  • Rooms: {Room.objects.count()}")
    print(f"  • IPD Stays: {InpatientStay.objects.count()}")
    print(f"  • QC Logs: {QCLog.objects.count()}")
    print("\nNow all pages will display data! 🎉")
    print("="*70 + "\n")

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
