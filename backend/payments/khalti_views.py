"""Khalti payment API views"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from .khalti_service import khalti_service
from .models import Payment
from audit.utils import log_audit_event

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_khalti_payment(request):
    """Initiate Khalti payment"""
    try:
        payment_id = request.data.get('payment_id')
        # Avoid evaluating settings.FRONTEND_URL when not present in test env
        return_url = request.data.get('return_url')
        if not return_url:
            frontend = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return_url = f"{frontend}/billing/khalti-success"
        
        if not payment_id:
            return Response({'error': 'payment_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Verify ownership
        if payment.patient.user != request.user and request.user.role != 'ADMIN':
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if payment.status == 'PAID':
            return Response({'error': 'Already paid'}, status=status.HTTP_400_BAD_REQUEST)

        if payment.payment_method != 'KHALTI':
            payment.payment_method = 'KHALTI'
            payment.save(update_fields=['payment_method', 'updated_at'])
        
        result = khalti_service.initiate_payment(
            payment_id=payment_id,
            amount=float(payment.amount),
            return_url=return_url
        )
        
        if result['success']:
            log_audit_event(user=request.user, action='KHALTI_INITIATED', details=f'Payment {payment_id}')
            return Response({
                **result,
                'payment_id': payment.id,
                'appointment_id': payment.appointment_id,
                'payment_amount': float(payment.amount),
                'payment_status': payment.status,
            })
        else:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_khalti_payment(request):
    """Verify Khalti payment"""
    try:
        pidx = request.data.get('pidx')
        payment_id = request.data.get('payment_id')
        
        if not pidx or not payment_id:
            return Response({'error': 'pidx and payment_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        payment = get_object_or_404(Payment, id=payment_id)
        
        if payment.patient.user != request.user and request.user.role != 'ADMIN':
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        result = khalti_service.verify_payment(pidx)
        
        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update payment if completed
        if result['status'] == 'Completed':
            payment.status = 'PAID'
            payment.khalti_pidx = pidx
            payment.khalti_mobile = result.get('mobile')
            payment.amount_paid = payment.amount
            payment.paid_at = timezone.now()
            payment.save()
            
            # Mark appointment as CONFIRMED after successful payment
            if payment.appointment and payment.appointment.status == 'PENDING':
                payment.appointment.status = 'CONFIRMED'
                payment.appointment.save(update_fields=['status'])
            
            log_audit_event(user=request.user, action='KHALTI_VERIFIED', details=f'Payment {payment_id}')
            
            return Response({
                'success': True,
                'status': 'Completed',
                'message': 'Payment successful',
                'payment_id': payment.id,
                'appointment_id': payment.appointment_id,
                'payment_status': payment.status,
            })
        else:
            return Response({
                'success': False,
                'status': result['status'],
                'payment_id': payment.id,
                'appointment_id': payment.appointment_id,
            })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
