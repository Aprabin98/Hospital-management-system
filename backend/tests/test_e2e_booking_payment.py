import pytest
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from clinical.models import Doctor, Specialization, Shift, DoctorSchedule
from payments.models import Payment

User = get_user_model()


@pytest.mark.django_db
def test_end_to_end_booking_and_payment(monkeypatch):
    """ST-001: Registration -> Login -> Book appointment -> Initiate payment (mock Khalti)"""
    client = APIClient()

    # Register patient via API
    reg_data = {
        'email': 'e2e_patient@example.com',
        'password': 'strongpass123',
        'first_name': 'E2E',
        'last_name': 'Patient'
    }
    resp = client.post('/api/auth/register/', reg_data, format='json')
    assert resp.status_code == 201

    # Login to get token
    login_resp = client.post('/api/auth/login/', {'email': reg_data['email'], 'password': reg_data['password']})
    assert login_resp.status_code == 200
    token = login_resp.data.get('token') or login_resp.data.get('access')
    assert token
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # Create a doctor (admin-like creation via ORM)
    doc_user = User.objects.create_user(email='doc1@example.com', username='doc1', password='docpass', role='DOCTOR', is_active=True)
    # specialization optional
    spec = Specialization.objects.create(name='General')
    doctor = Doctor.objects.create(user=doc_user, specialization=spec)

    # Create a shift and schedule for tomorrow
    booking_date = timezone.now().date() + timedelta(days=1)
    shift = Shift.objects.create(name='TestShift', start_time='09:00', end_time='17:00', slot_duration=30)
    day_name = booking_date.strftime('%A')[:3].upper()
    DoctorSchedule.objects.create(doctor=doctor, day=day_name, shift=shift, is_active=True)

    # Patient books appointment on available slot 09:00
    appt_data = {
        'doctor': doctor.id,
        'date': booking_date.isoformat(),
        'start_time': '09:00'
    }
    appt_resp = client.post('/api/appointments/create/', appt_data, format='json')
    assert appt_resp.status_code == 201
    appt = appt_resp.data

    # Create payment for appointment
    # Refresh patient profile
    user = User.objects.get(email=reg_data['email'])
    patient_profile = user.patient_profile
    payment = Payment.objects.create(patient=patient_profile, amount=1500.00, status='UNPAID')

    # Mock khalti_service.initiate_payment to avoid external call
    def fake_initiate(payment_id, amount, return_url):
        return {'success': True, 'payment_url': 'https://khalti/pay/123', 'transaction_uuid': 'txn-e2e-1'}

    monkeypatch.setattr('payments.khalti_service.khalti_service.initiate_payment', fake_initiate)

    pay_resp = client.post('/payments/khalti/initiate/', {'payment_id': payment.id, 'return_url': 'http://localhost/'}, format='json')
    assert pay_resp.status_code == 200

    payment.refresh_from_db()
    assert payment.khalti_transaction_id is not None
