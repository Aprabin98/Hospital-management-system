import requests
import logging
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class KhaltiPaymentService:
    def __init__(self):
        self.public_key = settings.KHALTI_PUBLIC_KEY
        self.secret_key = settings.KHALTI_SECRET_KEY
        self.api_url = settings.KHALTI_API_URL
        
    def initiate_payment(self, payment_id, amount, return_url):
        """Initiate Khalti payment"""
        try:
            from .models import Payment
            payment = Payment.objects.get(id=payment_id)
            
            amount_paisa = int(amount * 100)  # Convert NPR to paisa
            
            payload = {
                'public_key': self.public_key,
                'transaction_uuid': f'HMS-{payment_id}-{timezone.now().timestamp()}',
                'total_amount': amount_paisa,
                'transaction_narrative': f'Hospital Payment #{payment_id}',
                'customer_name': payment.patient.user.get_full_name(),
                'customer_email': payment.patient.user.email,
                'return_url': return_url,
            }
            
            response = requests.post(
                f'{self.api_url}epayment/initiate/',
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                payment.khalti_transaction_id = data.get('transaction_uuid')
                payment.payment_method = 'KHALTI'
                payment.save()
                
                return {
                    'success': True,
                    'payment_url': data.get('payment_url'),
                    'transaction_id': data.get('transaction_uuid'),
                }
            else:
                logger.error(f"Khalti error: {response.text}")
                return {'success': False, 'error': 'Failed to initiate payment'}
        except Payment.DoesNotExist:
            return {'success': False, 'error': 'Payment not found'}
        except Exception as e:
            logger.error(f"Khalti service error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_payment(self, pidx):
        """Verify Khalti payment status"""
        try:
            headers = {'Authorization': f'Key {self.secret_key}'}
            
            response = requests.post(
                f'{self.api_url}epayment/lookup/',
                json={'pidx': pidx},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'status': data.get('status'),
                    'transaction_id': data.get('transaction_uuid'),
                    'amount': data.get('total_amount'),
                    'mobile': data.get('mobile_number'),
                }
            else:
                return {'success': False, 'error': 'Verification failed'}
        except Exception as e:
            logger.error(f"Khalti verify error: {str(e)}")
            return {'success': False, 'error': str(e)}

khalti_service = KhaltiPaymentService()
