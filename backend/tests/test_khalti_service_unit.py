import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from payments.khalti_service import khalti_service
from payments.models import Payment

User = get_user_model()


@pytest.mark.django_db
def test_khalti_initiate_updates_payment(monkeypatch):
    """UT-013: khalti_service.initiate_payment returns success and updates Payment."""
    # Create user and patient profile via user registration signal
    user = User.objects.create_user(email='khalti_user@example.com', username='kuser', password='p', role='PATIENT')
    patient_profile = user.patient_profile

    payment = Payment.objects.create(
        patient=patient_profile,
        amount=1000.00,
        status='UNPAID'
    )

    # Ensure khalti_service has config for test
    monkeypatch.setattr(khalti_service, 'api_url', 'https://khalti.test/')
    monkeypatch.setattr(khalti_service, 'public_key', 'pub_test')

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        'payment_url': 'https://khalti.test/pay/abc',
        'transaction_uuid': 'txn-12345'
    }

    with patch('payments.khalti_service.requests.post', return_value=fake_response) as mock_post:
        result = khalti_service.initiate_payment(payment_id=payment.id, amount=float(payment.amount), return_url='http://localhost/')

    assert isinstance(result, dict)
    assert result.get('success') is True

    # Refresh payment from DB
    payment.refresh_from_db()
    assert payment.khalti_transaction_id is not None
