"""
User Seeding Script - Creates test users for all roles and basic test data
Run with: python seed_users.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from users.models import User, PatientProfile
from clinical.models import Doctor, Specialization
from django.utils import timezone

# Define test users
TEST_USERS = [
    {
        'email': 'admin@hms.test',
        'name': 'Admin User',
        'password': 'Admin@123456',
        'role': 'ADMIN',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'email': 'doctor@hms.test',
        'name': 'Dr. John Smith',
        'password': 'Doctor@123456',
        'role': 'DOCTOR',
        'is_staff': True,
    },
    {
        'email': 'nurse@hms.test',
        'name': 'Sarah Johnson',
        'password': 'Nurse@123456',
        'role': 'NURSE',
        'is_staff': True,
    },
    {
        'email': 'lab_tech@hms.test',
        'name': 'Mike Wilson',
        'password': 'LabTech@123456',
        'role': 'LAB_TECHNICIAN',
        'is_staff': True,
    },
    {
        'email': 'pharmacist@hms.test',
        'name': 'Emma Davis',
        'password': 'Pharmacist@123456',
        'role': 'PHARMACIST',
        'is_staff': True,
    },
    {
        'email': 'receptionist@hms.test',
        'name': 'Lisa Brown',
        'password': 'Receptionist@123456',
        'role': 'RECEPTIONIST',
        'is_staff': True,
    },
    {
        'email': 'patient@hms.test',
        'name': 'Robert Miller',
        'password': 'Patient@123456',
        'role': 'PATIENT',
        'is_staff': False,
    },
    {
        'email': 'patient2@hms.test',
        'name': 'Mary Taylor',
        'password': 'Patient@123456',
        'role': 'PATIENT',
        'is_staff': False,
    },
]

def create_users():
    """Create test users"""
    print("\n" + "="*60)
    print("SEEDING TEST USERS")
    print("="*60 + "\n")
    
    created_count = 0
    for user_data in TEST_USERS:
        email = user_data['email']
        full_name = user_data.pop('name')
        password = user_data.pop('password')
        
        # Split name into first and last
        name_parts = full_name.split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                **user_data,
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
            }
        )

        user.is_active = True
        user.username = email.split('@')[0]
        user.first_name = first_name
        user.last_name = last_name
        user.role = user_data['role']
        user.is_staff = user_data.get('is_staff', False)
        user.is_superuser = user_data.get('is_superuser', False)
        user.set_password(password)
        user.save()

        if created:
            created_count += 1
            status = "✅ CREATED"
        else:
            status = "♻️ UPDATED"
        
        print(f"{status} | {user.email:30} | Role: {user.role:15} | Name: {first_name} {last_name}")
        
        # Create PatientProfile for patient users
        if user.role == 'PATIENT':
            PatientProfile.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': full_name,
                    'date_of_birth': timezone.now().date(),
                    'phone': '+1-555-0100',
                    'gender': 'M' if user.email.startswith('r') else 'F',
                }
            )
    
    print(f"\n✅ Total users created: {created_count}")
    
    # Create doctor profile if doctor role exists
    doctor_user = User.objects.filter(email='doctor@hms.test').first()
    if doctor_user:
        spec, _ = Specialization.objects.get_or_create(name='General Medicine')
        doctor, created = Doctor.objects.get_or_create(
            user=doctor_user,
            defaults={
                'specialization': spec,
                'consultation_fee': 500,
                'experience_years': 10,
                'is_available': True,
            }
        )
        if created:
            print(f"✅ Created Doctor profile for {doctor_user.email}")
        else:
            print(f"⏭️  Doctor profile exists for {doctor_user.email}")

if __name__ == '__main__':
    try:
        create_users()
        print("\n" + "="*60)
        print("✅ USER SEEDING COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nTest User Credentials:")
        print("-" * 60)
        for user in TEST_USERS:
            email = user['email']
            password_hint = "Admin@123456" if user['role'] == 'ADMIN' else "Doctor@123456" if user['role'] == 'DOCTOR' else "[Role]@123456"
            print(f"Email: {email:30} | Password: {password_hint}")
        print("-" * 60 + "\n")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
