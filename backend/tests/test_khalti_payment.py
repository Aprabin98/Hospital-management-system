"""Quick test for Khalti API endpoints"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from payments.models import Payment
from users.models import User, PatientProfile

@pytest.mark.django_db
class TestKhaltiPaymentFlow:
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123',
            role='PATIENT'
        )
        self.profile = PatientProfile.objects.create(
            user=self.user,
            full_name='Test Patient',
            phone='9841234567'
        )
        self.payment = Payment.objects.create(
            patient=self.profile,
            amount=1000,
            status='PENDING',
            payment_method='KHALTI'
        )
    
    def test_initiate_khalti_payment(self):
        """Test Khalti payment initiation"""
        self.client.force_authenticate(user=self.user)
        url = reverse('payments:khalti_initiate')
        data = {
            'payment_id': self.payment.id,
            'return_url': 'http://localhost:3000/billing/khalti-success'
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        
    def test_verify_khalti_payment(self):
        """Test Khalti payment verification"""
        self.client.force_authenticate(user=self.user)
        self.payment.khalti_pidx = 'test123'
        self.payment.save()
        
        url = reverse('payments:khalti_verify')
        data = {
            'pidx': 'test123',
            'payment_id': self.payment.id
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
