from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from payments.models import Payment
from clinical.models import Specialization,Doctor,Shift,DoctorSchedule
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
client = APIClient()
reg = {'email':'dbg_patient@example.com','password':'dbgpass123','first_name':'Dbg','last_name':'Patient'}
r = client.post('/api/auth/register/', reg, format='json')
print('reg', r.status_code, getattr(r,'data',r.content))
login = client.post('/api/auth/login/', {'email':reg['email'],'password':reg['password']})
print('login', getattr(login,'status_code',None), getattr(login,'data',login.content))
token = login.data.get('token') or login.data.get('access')
client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

doc_user = User.objects.create_user(email='doc_dbg@example.com', username='doc_dbg', password='docpass', role='DOCTOR', is_active=True)
spec = Specialization.objects.create(name='GeneralDbg')
doctor = Doctor.objects.create(user=doc_user, specialization=spec)
booking_date = timezone.now().date() + timedelta(days=1)
shift = Shift.objects.create(name='S', start_time='09:00', end_time='17:00', slot_duration=30)
day_name = booking_date.strftime('%A')[:3].upper()
DoctorSchedule.objects.create(doctor=doctor, day=day_name, shift=shift, is_active=True)
appt = client.post('/api/appointments/create/', {'doctor': doctor.id, 'date': booking_date.isoformat(), 'start_time': '09:00'}, format='json')
print('appt', getattr(appt,'status_code',None), getattr(appt,'data',appt.content))
user = User.objects.get(email=reg['email'])
patient_profile = user.patient_profile
payment = Payment.objects.create(patient=patient_profile, amount=1500.0, status='UNPAID')
import payments.khalti_service as ks
ks.khalti_service.initiate_payment = lambda payment_id, amount, return_url: {'success': True, 'payment_url': 'https://khalti/pay/1', 'transaction_uuid': 'txn1'}
resp = client.post('/payments/khalti/initiate/', {'payment_id': payment.id, 'return_url': 'http://localhost/'}, format='json')
print('resp', getattr(resp,'status_code',None), getattr(resp,'data',resp.content))
