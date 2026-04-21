"""API Views for Phase 7: Finance & Insurance Maturity"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404
from datetime import timedelta

from .models import (
    Invoice, InvoiceLineItem, InsuranceClaim, ClaimAuditLog,
    DenialRework, InsurancePreAuth, InsuranceVerification
)
from .api_serializers import (
    InvoiceSerializer, InvoiceLineItemSerializer,
    InsuranceClaimSerializer, DenialReworkSerializer,
    InsurancePreAuthSerializer, InsuranceVerificationSerializer
)
from audit.utils import log_audit_event


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    Invoice management for billing officers
    Endpoints:
    - POST /api/payments/invoices/ - Create new invoice
    - GET /api/payments/invoices/ - List invoices (filtered by role)
    - GET /api/payments/invoices/{id}/ - Retrieve invoice
    - PUT /api/payments/invoices/{id}/ - Update invoice
    - POST /api/payments/invoices/{id}/finalize/ - Convert proforma to final
    - POST /api/payments/invoices/{id}/mark_paid/ - Mark invoice as paid
    """
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return Invoice.objects.filter(patient__user=user)
        elif user.role in ['BILLING_OFFICER', 'INSURANCE_COORDINATOR', 'ADMIN']:
            return Invoice.objects.all()
        return Invoice.objects.none()
    
    def perform_create(self, serializer):
        invoice = serializer.save(created_by=self.request.user)
        invoice.invoice_number = f"INV-{invoice.id:06d}-{timezone.now().strftime('%Y%m%d')}"
        invoice.save()
        
        log_audit_event(
            action='CREATE',
            request=self.request,
            target=invoice,
            description=f'Invoice {invoice.invoice_number} created',
            metadata={'invoice_id': invoice.id, 'invoice_type': invoice.invoice_type}
        )
    
    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        """Convert proforma invoice to final invoice"""
        invoice = self.get_object()
        
        if request.user.role not in ['BILLING_OFFICER', 'ADMIN']:
            return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if invoice.invoice_type != 'PROFORMA':
            return Response(
                {'detail': 'Only proforma invoices can be finalized'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice.invoice_type = 'FINAL'
        invoice.issued_date = timezone.now().date()
        invoice.status = 'ISSUED'
        invoice.due_date = timezone.now().date() + timedelta(days=30)
        invoice.save()
        
        log_audit_event(
            action='UPDATE',
            request=request,
            target=invoice,
            description=f'Invoice {invoice.invoice_number} finalized',
            metadata={'invoice_id': invoice.id}
        )
        
        return Response(InvoiceSerializer(invoice).data)
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as fully or partially paid"""
        invoice = self.get_object()
        
        if request.user.role not in ['BILLING_OFFICER', 'ADMIN']:
            return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        amount_paid = request.data.get('amount_paid')
        if not amount_paid:
            return Response(
                {'detail': 'amount_paid is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice.amount_paid += float(amount_paid)
        
        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = 'PAID'
            invoice.amount_paid = invoice.total_amount
        else:
            invoice.status = 'PARTIALLY_PAID'
        
        invoice.save()
        
        log_audit_event(
            action='UPDATE',
            request=request,
            target=invoice,
            description=f'Invoice {invoice.invoice_number} payment recorded',
            metadata={'invoice_id': invoice.id, 'amount_paid': amount_paid}
        )
        
        return Response(InvoiceSerializer(invoice).data)


class InsuranceClaimViewSet(viewsets.ModelViewSet):
    """
    Insurance claim management
    Endpoints:
    - POST /api/payments/claims/ - Create new claim
    - GET /api/payments/claims/ - List claims
    - GET /api/payments/claims/{id}/ - Retrieve claim
    - POST /api/payments/claims/{id}/submit/ - Submit claim to insurer
    - POST /api/payments/claims/{id}/approve/ - Approve claim
    - POST /api/payments/claims/{id}/reject/ - Reject claim
    """
    serializer_class = InsuranceClaimSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return InsuranceClaim.objects.filter(patient__user=user)
        elif user.role in ['INSURANCE_COORDINATOR', 'BILLING_OFFICER', 'ADMIN']:
            return InsuranceClaim.objects.all()
        return InsuranceClaim.objects.none()
    
    def perform_create(self, serializer):
        claim = serializer.save()
        claim.claim_number = f"CLM-{claim.id:06d}-{timezone.now().strftime('%Y%m%d')}"
        claim.save()
        
        # Create initial audit log
        ClaimAuditLog.objects.create(
            claim=claim,
            old_status='',
            new_status='DRAFT',
            changed_by=self.request.user,
            notes='Claim created'
        )
        
        log_audit_event(
            action='CREATE',
            request=self.request,
            target=claim,
            description=f'Claim {claim.claim_number} created',
            metadata={'claim_id': claim.id}
        )
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit claim to insurance company"""
        claim = self.get_object()
        
        if request.user.role not in ['INSURANCE_COORDINATOR', 'ADMIN']:
            return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if claim.status != 'DRAFT':
            return Response(
                {'detail': f'Can only submit draft claims, current status: {claim.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = claim.status
        claim.status = 'SUBMITTED'
        claim.submitted_at = timezone.now()
        claim.submitted_by = request.user
        claim.submission_reference = request.data.get('submission_reference', '')
        claim.submission_notes = request.data.get('submission_notes', '')
        claim.save()
        
        # Log status change
        ClaimAuditLog.objects.create(
            claim=claim,
            old_status=old_status,
            new_status=claim.status,
            changed_by=request.user,
            notes=f'Submitted to insurer with reference: {claim.submission_reference}'
        )
        
        log_audit_event(
            action='UPDATE',
            request=request,
            target=claim,
            description=f'Claim {claim.claim_number} submitted to insurer',
            metadata={'claim_id': claim.id, 'reference': claim.submission_reference}
        )
        
        return Response(InsuranceClaimSerializer(claim).data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve insurance claim"""
        claim = self.get_object()
        
        if request.user.role not in ['INSURANCE_COORDINATOR', 'ADMIN']:
            return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if claim.status in ['APPROVED', 'REJECTED', 'DENIED']:
            return Response(
                {'detail': f'Claim is already {claim.status.lower()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = claim.status
        approved_amount = request.data.get('approved_amount')
        
        if float(approved_amount or 0) < claim.claimed_amount:
            claim.status = 'APPROVED_WITH_REDUCTION'
            claim.reduction_reason = request.data.get('reduction_reason', '')
        else:
            claim.status = 'APPROVED'
        
        claim.approved_amount = approved_amount or claim.claimed_amount
        claim.approved_at = timezone.now()
        claim.save()
        
        # Log status change
        ClaimAuditLog.objects.create(
            claim=claim,
            old_status=old_status,
            new_status=claim.status,
            changed_by=request.user,
            notes=f'Approved for amount: Rs.{claim.approved_amount}'
        )
        
        log_audit_event(
            action='UPDATE',
            request=request,
            target=claim,
            description=f'Claim {claim.claim_number} approved',
            metadata={'claim_id': claim.id, 'approved_amount': approved_amount}
        )
        
        return Response(InsuranceClaimSerializer(claim).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject insurance claim"""
        claim = self.get_object()
        
        if request.user.role not in ['INSURANCE_COORDINATOR', 'ADMIN']:
            return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        old_status = claim.status
        reason = request.data.get('reason', 'No reason provided')
        
        claim.status = 'REJECTED'
        claim.save()
        
        # Create denial rework if this was previously submitted
        if old_status == 'SUBMITTED':
            DenialRework.objects.create(
                claim=claim,
                original_denial_reason=reason,
                status='PENDING_REVIEW'
            )
        
        # Log status change
        ClaimAuditLog.objects.create(
            claim=claim,
            old_status=old_status,
            new_status=claim.status,
            changed_by=request.user,
            notes=f'Rejected. Reason: {reason}'
        )
        
        log_audit_event(
            action='UPDATE',
            request=request,
            target=claim,
            description=f'Claim {claim.claim_number} rejected',
            metadata={'claim_id': claim.id, 'reason': reason}
        )
        
        return Response(InsuranceClaimSerializer(claim).data)


class DenialReworkViewSet(viewsets.ModelViewSet):
    """
    Denial rework queue management
    Endpoints:
    - GET /api/payments/denial-reworks/ - List pending denials
    - GET /api/payments/denial-reworks/{id}/ - Get rework details
    - POST /api/payments/denial-reworks/{id}/assign/ - Assign to billing officer
    - POST /api/payments/denial-reworks/{id}/resubmit/ - Resubmit corrected claim
    """
    serializer_class = DenialReworkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['INSURANCE_COORDINATOR', 'BILLING_OFFICER', 'ADMIN']:
            return DenialRework.objects.all()
        return DenialRework.objects.none()
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending denial reworks"""
        reworks = self.get_queryset().filter(status='PENDING_REVIEW')
        serializer = self.get_serializer(reworks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign rework to a billing officer"""
        rework = self.get_object()
        assigned_to_id = request.data.get('assigned_to_id')
        
        from users.models import User
        assigned_user = get_object_or_404(User, id=assigned_to_id, role='BILLING_OFFICER')
        
        rework.assigned_to = assigned_user
        rework.status = 'UNDER_CORRECTION'
        rework.save()
        
        log_audit_event(
            action='UPDATE',
            request=request,
            target=rework,
            description=f'Rework assigned to {assigned_user.email}',
            metadata={'rework_id': rework.id, 'assigned_to': assigned_user.email}
        )
        
        return Response(DenialReworkSerializer(rework).data)
    
    @action(detail=True, methods=['post'])
    def resubmit(self, request, pk=None):
        """Resubmit corrected claim"""
        rework = self.get_object()
        
        if rework.status != 'UNDER_CORRECTION':
            return Response(
                {'detail': 'Only under-correction reworks can be resubmitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        claim = rework.claim
        claim.status = 'RESUBMITTED'
        claim.submitted_at = timezone.now()
        claim.submission_notes = request.data.get('submission_notes', '')
        claim.save()
        
        rework.status = 'RESUBMITTED'
        rework.resubmit_date = timezone.now().date()
        rework.correction_notes = request.data.get('correction_notes', '')
        rework.save()
        
        ClaimAuditLog.objects.create(
            claim=claim,
            old_status='REJECTED',
            new_status='RESUBMITTED',
            changed_by=request.user,
            notes=f'Resubmitted after denial correction: {rework.correction_notes}'
        )
        
        log_audit_event(
            action='UPDATE',
            request=request,
            target=rework,
            description=f'Claim resubmitted after denial correction',
            metadata={'rework_id': rework.id, 'claim_id': claim.id}
        )
        
        return Response({
            'rework': DenialReworkSerializer(rework).data,
            'claim': InsuranceClaimSerializer(claim).data
        })


class InsurancePreAuthViewSet(viewsets.ModelViewSet):
    """
    Insurance pre-authorization management
    Endpoints:
    - POST /api/payments/pre-auths/ - Request pre-authorization
    - GET /api/payments/pre-auths/ - List pre-authorizations
    - POST /api/payments/pre-auths/{id}/approve/ - Approve pre-auth
    """
    serializer_class = InsurancePreAuthSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return InsurancePreAuth.objects.filter(patient__user=user)
        elif user.role in ['INSURANCE_COORDINATOR', 'BILLING_OFFICER', 'ADMIN']:
            return InsurancePreAuth.objects.all()
        return InsurancePreAuth.objects.none()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve pre-authorization request"""
        pre_auth = self.get_object()
        
        if request.user.role not in ['INSURANCE_COORDINATOR', 'ADMIN']:
            return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if pre_auth.status != 'REQUESTED':
            return Response(
                {'detail': f'Pre-auth is already {pre_auth.status.lower()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pre_auth.status = 'APPROVED'
        pre_auth.approved_amount = request.data.get('approved_amount', pre_auth.estimated_amount)
        pre_auth.approved_at = timezone.now()
        pre_auth.pre_auth_number = f"PA-{pre_auth.id:06d}-{timezone.now().strftime('%Y%m%d')}"
        pre_auth.save()
        
        log_audit_event(
            action='UPDATE',
            request=request,
            target=pre_auth,
            description=f'Pre-authorization approved: {pre_auth.pre_auth_number}',
            metadata={'pre_auth_id': pre_auth.id, 'approved_amount': pre_auth.approved_amount}
        )
        
        return Response(InsurancePreAuthSerializer(pre_auth).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def finance_dashboard_api(request):
    """
    Finance dashboard with KPIs
    Access: BILLING_OFFICER, INSURANCE_COORDINATOR, ADMIN
    """
    user = request.user
    if user.role not in ['BILLING_OFFICER', 'INSURANCE_COORDINATOR', 'ADMIN']:
        return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Claim status summary
    claims_by_status = InsuranceClaim.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('claimed_amount')
    )
    
    # Denial rate
    total_claims = InsuranceClaim.objects.count()
    denied_claims = InsuranceClaim.objects.filter(status__in=['DENIED', 'REJECTED']).count()
    denial_rate = (denied_claims / total_claims * 100) if total_claims > 0 else 0
    
    # Invoice metrics
    total_invoiced = Invoice.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_collected = Invoice.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
    collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0
    
    return Response({
        'claims_summary': {
            'total_claims': total_claims,
            'by_status': list(claims_by_status),
            'denial_rate': round(denial_rate, 2),
        },
        'invoice_summary': {
            'total_invoiced': float(total_invoiced),
            'total_collected': float(total_collected),
            'collection_rate': round(collection_rate, 2),
            'pending_invoices': Invoice.objects.filter(status='ISSUED').count(),
        },
        'aging_analysis': {
            'claims_over_30_days': InsuranceClaim.objects.filter(
                status='SUBMITTED',
                submitted_at__lte=timezone.now() - timedelta(days=30)
            ).count(),
            'claims_over_45_days': InsuranceClaim.objects.filter(
                status='SUBMITTED',
                submitted_at__lte=timezone.now() - timedelta(days=45)
            ).count(),
        },
        'pending_reworks': DenialRework.objects.filter(status='PENDING_REVIEW').count(),
    })


# Financial Reconciliation Reports

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_reconciliation_api(request):
    """
    Daily financial reconciliation report
    Access: BILLING_OFFICER, INSURANCE_COORDINATOR, ADMIN
    Query params: date (YYYY-MM-DD)
    """
    user = request.user
    if user.role not in ['BILLING_OFFICER', 'INSURANCE_COORDINATOR', 'ADMIN']:
        return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    from payments.reconciliation import FinancialReconciliation
    
    date_str = request.query_params.get('date')
    if date_str:
        try:
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return Response({'detail': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        date = None
    
    report = FinancialReconciliation.daily_reconciliation(date)
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_reconciliation_api(request):
    """
    Monthly financial reconciliation report
    Access: BILLING_OFFICER, INSURANCE_COORDINATOR, ADMIN
    Query params: year, month (1-12)
    """
    user = request.user
    if user.role not in ['BILLING_OFFICER', 'INSURANCE_COORDINATOR', 'ADMIN']:
        return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    from payments.reconciliation import FinancialReconciliation
    
    year = request.query_params.get('year')
    month = request.query_params.get('month')
    
    if year and month:
        try:
            year = int(year)
            month = int(month)
            if not (1 <= month <= 12):
                raise ValueError('Month must be 1-12')
        except:
            return Response({'detail': 'Invalid year or month'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        year = month = None
    
    report = FinancialReconciliation.monthly_reconciliation(year, month)
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def outstanding_receivables_api(request):
    """
    Outstanding receivables report with aging buckets
    Access: BILLING_OFFICER, INSURANCE_COORDINATOR, ADMIN
    """
    user = request.user
    if user.role not in ['BILLING_OFFICER', 'INSURANCE_COORDINATOR', 'ADMIN']:
        return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    from payments.reconciliation import FinancialReconciliation
    
    report = FinancialReconciliation.outstanding_receivables()
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def claim_status_report_api(request):
    """
    Insurance claim status report
    Access: BILLING_OFFICER, INSURANCE_COORDINATOR, ADMIN
    """
    user = request.user
    if user.role not in ['BILLING_OFFICER', 'INSURANCE_COORDINATOR', 'ADMIN']:
        return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    from payments.reconciliation import FinancialReconciliation
    
    report = FinancialReconciliation.claim_status_report()
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def provider_performance_api(request):
    """
    Insurance provider performance report
    Access: BILLING_OFFICER, INSURANCE_COORDINATOR, ADMIN
    """
    user = request.user
    if user.role not in ['BILLING_OFFICER', 'INSURANCE_COORDINATOR', 'ADMIN']:
        return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    from payments.reconciliation import FinancialReconciliation
    
    report = FinancialReconciliation.provider_performance_report()
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def refund_summary_api(request):
    """
    Refund processing summary
    Access: BILLING_OFFICER, INSURANCE_COORDINATOR, ADMIN
    """
    user = request.user
    if user.role not in ['BILLING_OFFICER', 'INSURANCE_COORDINATOR', 'ADMIN']:
        return Response({'detail': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    from payments.reconciliation import FinancialReconciliation
    
    report = FinancialReconciliation.refund_summary()
    return Response(report)
