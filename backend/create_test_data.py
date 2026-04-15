import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from users.models import User, PatientProfile
from clinical.models import Doctor
from rooms.models import Room, RoomBed, RoomAssignment
from heart_risk.models import HeartRiskAssessment
from django.utils import timezone

# Check if test user exists
patient_user = User.objects.filter(email="acharyaprabin507@gmail.com").first()

if patient_user:
    print(f"✓ Found patient user: {patient_user.email}")
    
    # Get or create patient profile
    patient_profile, created = PatientProfile.objects.get_or_create(user=patient_user)
    print(f"✓ Patient profile: {patient_profile.full_name if not created else 'Created new'}")
    
    # Get or create room
    room, _ = Room.objects.get_or_create(
        room_number="Test-101",
        defaults={
            "room_type": "GENERAL",
            "floor": "1",
            "capacity": 4,
            "is_active": True,
            "notes": "Test room for verification"
        }
    )
    print(f"✓ Room created: {room.room_number}")
    
    # Get or create bed
    bed, _ = RoomBed.objects.get_or_create(
        room=room,
        bed_number="A1",
        defaults={"status": "OCCUPIED"}
    )
    print(f"✓ Bed created: {bed.bed_number}")
    
    # Get doctor (first one available)
    doctor = Doctor.objects.first()
    
    # Create room assignment
    assignment, created = RoomAssignment.objects.get_or_create(
        patient=patient_profile,
        bed=bed,
        defaults={
            "doctor": doctor,
            "reason": "Test admission",
            "status": "ADMITTED",
            "admitted_at": timezone.now()
        }
    )
    
    if created:
        print(f"✓ Room assignment created for {patient_profile.full_name}")
    else:
        print(f"✓ Room assignment already exists for {patient_profile.full_name}")
    
    # Create heart risk assessment
    assessment, created = HeartRiskAssessment.objects.get_or_create(
        patient=patient_profile,
        defaults={
            "assessed_by": patient_user,
            "doctor": doctor,
            "age": 45,
            "sex": "M",
            "systolic_bp": 130,
            "diastolic_bp": 85,
            "total_cholesterol": 200,
            "fasting_blood_sugar": 100,
            "bmi": 25.5,
            "smoker": False,
            "diabetic": False,
            "family_history": False,
            "chest_pain": False,
            "sedentary_lifestyle": False,
            "risk_score": 45,
            "risk_level": "MEDIUM",
            "summary": "Moderate cardiovascular risk",
            "recommendations": "Maintain healthy lifestyle"
        }
    )
    
    if created:
        print(f"✓ Heart risk assessment created for {patient_profile.full_name}")
    else:
        print(f"✓ Heart risk assessment already exists for {patient_profile.full_name}")
    
    print(f"\n✅ Test data setup complete!")

else:
    print("✗ Patient user not found")
