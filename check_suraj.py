import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from users.models import PatientProfile
from appointments.models import Appointment

suraj = PatientProfile.objects.filter(full_name__icontains='suraj').first()
if suraj:
    print('SURAJ_FOUND=True')
    print('SURAJ_PHONE=', suraj.phone)
    print('SURAJ_USER_EMAIL=', suraj.user.email)
    print('SURAJ_PROFILE_ID=', suraj.id)
    
    # Check recent appointments for suraj
    recent_appts = Appointment.objects.filter(patient=suraj).order_by('-created_at')[:3]
    print('SURAJ_RECENT_APPOINTMENTS=', recent_appts.count())
    for appt in recent_appts:
        print(f'  ID={appt.id}, Doctor={appt.doctor.user.username}, Date={appt.date}, Status={appt.status}')
else:
    all_patients = list(PatientProfile.objects.all().values_list('full_name', 'phone', 'id'))
    print('SURAJ_FOUND=False')
    print('TOTAL_PATIENTS=', len(all_patients))
    print('PATIENTS=')
    for name, phone, pid in all_patients[:15]:
        print(f'  {name} | {phone} | ID={pid}')
