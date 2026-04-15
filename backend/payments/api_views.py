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

from .models import Payment, Refund, InsuranceVerification
from .api_serializers import PaymentSerializer, RefundSerializer
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
def insurance_list_api(request):
    """List insurance verifications for admin/receptionist or current patient."""
    user = request.user
    if user.role == 'PATIENT':
        queryset = InsuranceVerification.objects.filter(patient=user.patient_profile)
    elif user.role in ['ADMIN', 'RECEPTIONIST']:
        queryset = InsuranceVerification.objects.all().select_related('patient__user', 'verified_by')
    else:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    items = []
    for row in queryset[:300]:
        row.mark_expired_if_needed()
        items.append(
            {
                'id': row.id,
                'patient_id': row.patient_id,
                'patient': row.patient.full_name,
                'provider_name': row.provider_name,
                'policy_number': row.policy_number,
                'plan_name': row.plan_name,
                'coverage_percent': row.coverage_percent,
                'status': row.status,
                'valid_until': row.valid_until.isoformat() if row.valid_until else None,
                'verification_notes': row.verification_notes,
                'external_reference': row.external_reference,
            }
        )

    return Response({'count': len(items), 'results': items}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def refunds_admin_api(request):
    """List refund requests for admin/receptionist review."""
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    queryset = Refund.objects.select_related('payment__patient__user', 'payment__doctor__user').order_by('-created_at')
    status_filter = (request.query_params.get('status') or '').strip().upper()
    if status_filter in {'PENDING', 'APPROVED', 'REJECTED'}:
        queryset = queryset.filter(status=status_filter)

    items = []
    for refund in queryset[:300]:
        items.append(
            {
                'id': refund.id,
                'payment_id': refund.payment_id,
                'patient_name': refund.payment.patient.full_name,
                'doctor_name': refund.payment.doctor.user.username if refund.payment.doctor_id else None,
                'amount': float(refund.payment.amount),
                'reason': refund.reason,
                'status': refund.status,
                'notes': refund.notes,
                'created_at': refund.created_at.isoformat(),
                'refunded_at': refund.refunded_at.isoformat() if refund.refunded_at else None,
                'payment_status': refund.payment.status,
            }
        )

    return Response({'count': queryset.count(), 'results': items}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def insurance_create_api(request):
    """Create insurance verification request for patient."""
    if request.user.role != 'PATIENT':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    provider_name = (request.data.get('provider_name') or '').strip()
    policy_number = (request.data.get('policy_number') or '').strip()
    if not provider_name or not policy_number:
        return Response({'detail': 'provider_name and policy_number are required.'}, status=status.HTTP_400_BAD_REQUEST)

    record = InsuranceVerification.objects.create(
        patient=request.user.patient_profile,
        provider_name=provider_name,
        policy_number=policy_number,
        plan_name=(request.data.get('plan_name') or '').strip(),
        coverage_percent=request.data.get('coverage_percent') or 0,
        valid_until=request.data.get('valid_until') or None,
        status='PENDING',
    )

    return Response({'id': record.id, 'status': record.status}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def insurance_verify_api(request, insurance_id):
    """Verify/reject insurance request for admin or receptionist."""
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    insurance = get_object_or_404(InsuranceVerification, pk=insurance_id)
    next_status = (request.data.get('status') or '').strip().upper()
    if next_status not in {'PENDING', 'VERIFIED', 'REJECTED', 'EXPIRED'}:
        return Response({'detail': 'status must be one of PENDING, VERIFIED, REJECTED, EXPIRED.'}, status=status.HTTP_400_BAD_REQUEST)

    insurance.status = next_status
    insurance.verification_notes = (request.data.get('verification_notes') or insurance.verification_notes or '').strip()
    insurance.external_reference = (request.data.get('external_reference') or insurance.external_reference or '').strip()
    insurance.verified_by = request.user
    insurance.verified_at = timezone.now()
    insurance.save(update_fields=['status', 'verification_notes', 'external_reference', 'verified_by', 'verified_at', 'updated_at'])

    return Response({'id': insurance.id, 'status': insurance.status}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refund_request_api(request, payment_id):
    """
    POST: Patient requests a refund for a paid payment.
    - Reason: Required
    - Only PAID payments can be refunded
    - Cannot create duplicate refund requests
    """
    payment = get_object_or_404(Payment, pk=payment_id)
    user = request.user
    
    # Security check - only patient can request refund
    if user.role != 'PATIENT':
        return Response(
            {'detail': 'Only patients can request refunds.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if payment.patient != user.patient_profile:
        return Response(
            {'detail': 'This payment does not belong to you.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Payment must be PAID to request refund
    if payment.status != 'PAID':
        return Response(
            {'detail': 'Only paid payments can be refunded.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if refund already exists
    if hasattr(payment, 'refund'):
        return Response(
            {'detail': 'A refund request already exists for this payment.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response(
            {'detail': 'Reason is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create refund request
    refund = Refund.objects.create(
        payment=payment,
        reason=reason,
        status='PENDING'
    )

    log_audit_event(
        action='CREATE',
        request=request,
        target=refund,
        description=f'Patient requested refund for payment #{payment.id}.',
        metadata={
            'payment_id': payment.id,
            'refund_id': refund.id,
            'requested_by_role': user.role,
        },
    )
    
    serializer = RefundSerializer(refund)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refund_manage_api(request, payment_id):
    """
    POST: Approve or reject a refund request.
    Access: ADMIN only
    """
    user = request.user
    if user.role != 'ADMIN':
        log_audit_event(
            action='SECURITY',
            request=request,
            target=payment_id and {'model_name': 'payments.payment', 'object_id': str(payment_id), 'object_repr': f'Payment #{payment_id}'},
            description=f'Blocked refund management attempt for payment #{payment_id}.',
            metadata={
                'attempted_status': (request.data.get('status') or '').strip().upper(),
                'actor_role': user.role,
            },
        )
        return Response(
            {'detail': 'Only admin can manage refund requests.'},
            status=status.HTTP_403_FORBIDDEN
        )

    payment = get_object_or_404(Payment, pk=payment_id)

    if not hasattr(payment, 'refund'):
        return Response(
            {'detail': 'No refund request exists for this payment.'},
            status=status.HTTP_404_NOT_FOUND
        )

    refund = payment.refund
    action = (request.data.get('status') or '').strip().upper()
    notes = (request.data.get('notes') or '').strip()

    if action not in ['APPROVED', 'REJECTED']:
        return Response(
            {'detail': 'Status must be either APPROVED or REJECTED.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if refund.status != 'PENDING':
        return Response(
            {'detail': f'Refund is already {refund.status.lower()}.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    refund.status = action
    if notes:
        refund.notes = notes

    if action == 'APPROVED':
        refund.refunded_at = timezone.now()
        payment.status = 'REFUNDED'
        payment.save(update_fields=['status', 'updated_at'])

    refund.save()

    log_audit_event(
        action='UPDATE',
        request=request,
        target=refund,
        description=f'Refund for payment #{payment.id} set to {action}.',
        metadata={
            'payment_id': payment.id,
            'refund_id': refund.id,
            'refund_status': refund.status,
            'payment_status': payment.status,
            'actor_role': user.role,
        },
    )

    return Response({
        'message': f'Refund {action.lower()} successfully.',
        'refund': RefundSerializer(refund).data,
        'payment_status': payment.status,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_revenue_summary_api(request):
    """
    GET: Revenue analytics for billing admin panel.
    Access: ADMIN only
    """
    user = request.user
    if user.role != 'ADMIN':
        return Response(
            {'detail': 'Only admin can access revenue summary.'},
            status=status.HTTP_403_FORBIDDEN
        )

    paid_payments = Payment.objects.filter(status='PAID')
    approved_refunds = Refund.objects.filter(status='APPROVED')

    total_revenue = float(paid_payments.aggregate(total=Sum('amount'))['total'] or 0)
    total_transactions = paid_payments.count()
    total_refunded_amount = float(approved_refunds.aggregate(total=Sum('payment__amount'))['total'] or 0)
    pending_refund_count = Refund.objects.filter(status='PENDING').count()

    revenue_by_type = list(
        paid_payments.values('payment_type')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )

    for item in revenue_by_type:
        item['total'] = float(item['total'] or 0)

    return Response({
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'total_refunded_amount': total_refunded_amount,
        'pending_refund_count': pending_refund_count,
        'net_revenue': total_revenue - total_refunded_amount,
        'revenue_by_payment_type': revenue_by_type,
    })
