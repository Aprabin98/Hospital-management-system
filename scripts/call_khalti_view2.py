from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from payments.khalti_views import initiate_khalti_payment
from payments.models import Payment
from clinical.models import Specialization, Doctor
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

user, created = User.objects.get_or_create(email='dbg_patient3@example.com', defaults={'username':'dbg3','role':'PATIENT','is_active':True})
patient_profile = getattr(user, 'patient_profile', None)

doc_user, _ = User.objects.get_or_create(email='doc_call2@example.com', defaults={'username':'doccall2','role':'DOCTOR','is_active':True})
spec, _ = Specialization.objects.get_or_create(name='Gen2')
doctor, _ = Doctor.objects.get_or_create(user=doc_user, specialization=spec)

payment = Payment.objects.create(patient=patient_profile, amount=1000.0, status='UNPAID')

import payments.khalti_service as ks
ks.khalti_service.initiate_payment = lambda payment_id, amount, return_url: {'success': True, 'payment_url':'https://khalti/pay/1','transaction_uuid':'txn1'}

factory = APIRequestFactory()
request = factory.post('/payments/khalti/initiate/', {'payment_id': payment.id, 'return_url': 'http://localhost/'}, format='json')
request.META['HTTP_HOST'] = 'localhost'
force_authenticate(request, user=user)
resp = initiate_khalti_payment(request)
print('status', resp.status_code)
try:
    print('data', getattr(resp, 'data', resp.content))
except Exception as e:
    print('error accessing data:', e)
    print('raw content:', getattr(resp, 'content', None))
