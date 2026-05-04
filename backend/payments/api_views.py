"""API views for Payment functionality"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count
from django.core.files.storage import default_storage
from django.utils import timezone

from .models import Payment
from .api_serializers import PaymentSerializer
from .utils import generate_receipt_pdf
from audit.utils import log_audit_event


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payments_list_api(request):
    """
    GET: List patient's payments or all payments for admin.
    Role-based filtering:
    - PATIENT: Only their own payments
    - ADMIN/RECEPTIONIST: All payments
    """
    user = request.user
    
    if user.role == 'PATIENT':
        payments = Payment.objects.filter(
            patient=user.patient_profile
        ).select_related(
            'appointment', 'lab_booking__template', 'doctor__user'
        ).order_by('-created_at')
    elif user.role in ['ADMIN', 'RECEPTIONIST']:
        payments = Payment.objects.all().select_related(
            'appointment', 'lab_booking__template', 'doctor__user', 'patient__user'
        ).order_by('-created_at')
    else:
        return Response(
            {'detail': 'Access denied.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Filter by status if provided
    status_filter = request.query_params.get('status')
    if status_filter and status_filter in dict(Payment.STATUS_CHOICES):
        payments = payments.filter(status=status_filter)
    
    # Filter by payment type if provided
    payment_type = request.query_params.get('payment_type')
    if payment_type and payment_type in dict(Payment.PAYMENT_TYPE_CHOICES):
        payments = payments.filter(payment_type=payment_type)
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    paginated_payments = payments[start:end]
    
    # Calculate statistics
    total_paid = payments.filter(status='PAID').aggregate(total=Sum('amount'))['total'] or 0
    total_unpaid = payments.filter(status__in=['UNPAID', 'OVERDUE']).aggregate(total=Sum('amount'))['total'] or 0
    
    serializer = PaymentSerializer(paginated_payments, many=True)
    
    return Response({
        'count': payments.count(),
        'page': page,
        'page_size': page_size,
        'total_paid': float(total_paid),
        'total_unpaid': float(total_unpaid),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_detail_api(request, payment_id):
    """
    GET: Retrieve payment details.
    Security: Patient can only view own payments.
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    user = request.user
    
    # Security check
    if user.role == 'PATIENT':
        if payment.patient != user.patient_profile:
            return Response(
                {'detail': 'Access denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
    elif user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response(
            {'detail': 'Access denied.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = PaymentSerializer(payment)
    return Response(serializer.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_stats_api(request):
    """
    GET: Get payment statistics for dashboard.
    - PATIENT: Their own payment stats
    - ADMIN: Overall hospital stats
    """
    user = request.user
    
    if user.role == 'PATIENT':
        payments = Payment.objects.filter(patient=user.patient_profile)
    elif user.role in ['ADMIN', 'RECEPTIONIST']:
        payments = Payment.objects.all()
    else:
        return Response(
            {'detail': 'Access denied.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    stats = {
        'total_amount': float(payments.aggregate(Sum('amount'))['amount__sum'] or 0),
        'total_paid': float(payments.filter(status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0),
        'total_unpaid': float(payments.filter(status__in=['UNPAID', 'OVERDUE']).aggregate(Sum('amount'))['amount__sum'] or 0),
        'total_refunded': float(payments.filter(status='REFUNDED').aggregate(Sum('amount'))['amount__sum'] or 0),
        'payment_count': payments.count(),
        'paid_count': payments.filter(status='PAID').count(),
        'unpaid_count': payments.filter(status__in=['UNPAID', 'OVERDUE']).count(),
        'overdue_count': payments.filter(status='OVERDUE').count(),
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def invoice_download_api(request, payment_id):
    """
    GET: Download payment invoice PDF.
    Regenerates the receipt file when missing on disk.
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    user = request.user
    
    # Security check
    if user.role == 'PATIENT':
        if payment.patient != user.patient_profile:
            return Response(
                {'detail': 'Access denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
    elif user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response(
            {'detail': 'Access denied.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if payment.status != 'PAID':
        return Response(
            {'detail': 'Receipt is only available for paid payments.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    receipt_missing = (
        not payment.receipt_file
        or not payment.receipt_file.name
        or not default_storage.exists(payment.receipt_file.name)
    )

    if receipt_missing:
        generated = generate_receipt_pdf(payment)
        if not generated:
            return Response(
                {'detail': 'Failed to generate receipt PDF.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        payment.save(update_fields=['receipt_file', 'updated_at'])
    
    if payment.receipt_file and payment.receipt_file.name:
        response = FileResponse(
            payment.receipt_file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="receipt_{payment.id}.pdf"'
        return response
    
    return Response(
        {'detail': 'Receipt file is not available.'},
        status=status.HTTP_404_NOT_FOUND,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_mark_paid_api(request, payment_id):
    """
    POST: Mark a payment as PAID.
    Access: ADMIN, RECEPTIONIST
    """
    user = request.user
    if user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response(
            {'detail': 'Access denied.'},
            status=status.HTTP_403_FORBIDDEN
        )

    payment = get_object_or_404(Payment, pk=payment_id)

    if payment.status == 'PAID':
        return Response(
            {'detail': 'Payment is already marked as paid.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if payment.status == 'REFUNDED':
        return Response(
            {'detail': 'Refunded payments cannot be marked as paid again.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    payment_method = request.data.get('payment_method')
    notes = request.data.get('notes')

    if payment_method and payment_method in dict(Payment.METHOD_CHOICES):
        payment.payment_method = payment_method

    if notes:
        payment.notes = notes.strip()

    payment.amount_paid = payment.amount
    payment.status = 'PAID'
    payment.paid_at = timezone.now()

    # Generate receipt file for immediate download availability.
    generate_receipt_pdf(payment)
    payment.save()

    log_audit_event(
        action='UPDATE',
        request=request,
        target=payment,
        description=f'Payment #{payment.id} marked as paid via API.',
        metadata={
            'payment_id': payment.id,
            'new_status': payment.status,
            'payment_method': payment.payment_method,
            'updated_by_role': user.role,
        },
    )

    serializer = PaymentSerializer(payment)
    return Response(serializer.data)

