"""
Financial Reconciliation Reports - Phase 7
Path: backend/payments/reconciliation.py
Generates financial reports and reconciliation statements
"""

from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from payments.models import Invoice, InsuranceClaim, Refund, Payment, InsuranceVerification

class FinancialReconciliation:
    """Generate reconciliation reports for finance operations"""
    
    @staticmethod
    def daily_reconciliation(date=None):
        """Daily financial reconciliation"""
        if date is None:
            date = timezone.now().date()
        
        start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(date, datetime.max.time()))
        
        # Invoices issued today
        invoices_issued = Invoice.objects.filter(
            status='ISSUED',
            created_at__range=[start, end]
        ).aggregate(
            count=Count('id'),
            total=Sum('total_amount'),
            insurance_portion=Sum('insurance_amount'),
            patient_portion=Sum('patient_amount')
        )
        
        # Payments received today
        payments_received = Payment.objects.filter(
            paid_at__range=[start, end],
            status='COMPLETED'
        ).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Claims submitted today
        claims_submitted = InsuranceClaim.objects.filter(
            submitted_at__range=[start, end]
        ).aggregate(
            count=Count('id'),
            total=Sum('claimed_amount')
        )
        
        # Refunds processed today
        refunds_processed = Refund.objects.filter(
            status='COMPLETED',
            updated_at__range=[start, end]
        ).aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        return {
            'date': date.isoformat(),
            'invoices_issued': {
                'count': invoices_issued['count'] or 0,
                'total_amount': float(invoices_issued['total'] or 0),
                'insurance_portion': float(invoices_issued['insurance_portion'] or 0),
                'patient_portion': float(invoices_issued['patient_portion'] or 0)
            },
            'payments_received': {
                'count': payments_received['count'] or 0,
                'total_amount': float(payments_received['total'] or 0)
            },
            'claims_submitted': {
                'count': claims_submitted['count'] or 0,
                'total_amount': float(claims_submitted['total'] or 0)
            },
            'refunds_processed': {
                'count': refunds_processed['count'] or 0,
                'total_amount': float(refunds_processed['total'] or 0)
            }
        }
    
    @staticmethod
    def monthly_reconciliation(year=None, month=None):
        """Monthly financial reconciliation"""
        if year is None:
            today = timezone.now().date()
            year = today.year
            month = today.month
        
        start_date = timezone.make_aware(datetime(year, month, 1))
        if month == 12:
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            end_date = timezone.make_aware(datetime(year, month + 1, 1))
        
        # Total invoiced
        total_invoiced = Invoice.objects.filter(
            status__in=['ISSUED', 'PAID', 'PARTIALLY_PAID'],
            created_at__range=[start_date, end_date]
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        # Total collected
        total_collected = Invoice.objects.filter(
            created_at__range=[start_date, end_date]
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        
        # Total claimed
        total_claimed = InsuranceClaim.objects.filter(
            submitted_at__range=[start_date, end_date]
        ).aggregate(total=Sum('claimed_amount'))['total'] or Decimal('0')
        
        # Total approved
        total_approved = InsuranceClaim.objects.filter(
            status='APPROVED',
            approved_at__range=[start_date, end_date]
        ).aggregate(total=Sum('approved_amount'))['total'] or Decimal('0')
        
        # Total denied
        denied_count = InsuranceClaim.objects.filter(
            status__in=['DENIED', 'REJECTED'],
            submitted_at__range=[start_date, end_date]
        ).count()
        
        # By provider breakdown
        by_provider = InsuranceVerification.objects.filter(
            patient__invoice__created_at__range=[start_date, end_date]
        ).values('provider_name').annotate(
            invoice_count=Count('patient__invoice', distinct=True),
            total_amount=Sum('patient__invoice__total_amount')
        )
        
        return {
            'period': f"{year}-{month:02d}",
            'total_invoiced': float(total_invoiced),
            'total_collected': float(total_collected),
            'collection_percentage': float((total_collected / total_invoiced * 100) if total_invoiced > 0 else 0),
            'total_claimed': float(total_claimed),
            'total_approved': float(total_approved),
            'denial_count': denied_count,
            'denial_percentage': float((denied_count / max(InsuranceClaim.objects.filter(submitted_at__range=[start_date, end_date]).count(), 1) * 100)),
            'by_provider': [
                {
                    'provider': p['provider_name'],
                    'invoice_count': p['invoice_count'],
                    'total_amount': float(p['total_amount'] or 0)
                }
                for p in by_provider
            ]
        }
    
    @staticmethod
    def outstanding_receivables():
        """Report on outstanding payments"""
        outstanding = Invoice.objects.filter(
            status__in=['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']
        ).exclude(
            status='PAID'
        ).aggregate(
            total_outstanding=Sum(
                models.F('total_amount') - models.F('amount_paid'),
                output_field=models.DecimalField()
            ),
            count=Count('id')
        )
        
        # Aging buckets
        today = timezone.now().date()
        buckets = {
            'current': Invoice.objects.filter(
                status__in=['ISSUED', 'PARTIALLY_PAID'],
                due_date__gte=today
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
            '30_60_days': Invoice.objects.filter(
                status__in=['ISSUED', 'PARTIALLY_PAID'],
                due_date__lt=today,
                due_date__gte=today - timedelta(days=60)
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
            '60_90_days': Invoice.objects.filter(
                status__in=['ISSUED', 'PARTIALLY_PAID'],
                due_date__lt=today - timedelta(days=60),
                due_date__gte=today - timedelta(days=90)
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0'),
            'over_90_days': Invoice.objects.filter(
                status__in=['ISSUED', 'PARTIALLY_PAID'],
                due_date__lt=today - timedelta(days=90)
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        }
        
        return {
            'total_outstanding': float(outstanding['total_outstanding'] or 0),
            'invoice_count': outstanding['count'] or 0,
            'aging_buckets': {k: float(v) for k, v in buckets.items()}
        }
    
    @staticmethod
    def claim_status_report():
        """Report on claim statuses"""
        claims = InsuranceClaim.objects.values('status').annotate(
            count=Count('id'),
            total_claimed=Sum('claimed_amount'),
            total_approved=Sum('approved_amount')
        ).order_by('-count')
        
        pending_claims = InsuranceClaim.objects.filter(
            status__in=['SUBMITTED', 'PROCESSING', 'PENDING_MORE_INFO']
        )
        
        pending_days = []
        for claim in pending_claims:
            if claim.submitted_at:
                days = (timezone.now() - claim.submitted_at).days
                pending_days.append(days)
        
        avg_pending_days = sum(pending_days) / len(pending_days) if pending_days else 0
        
        return {
            'by_status': [
                {
                    'status': s['status'],
                    'count': s['count'],
                    'total_claimed': float(s['total_claimed'] or 0),
                    'total_approved': float(s['total_approved'] or 0)
                }
                for s in claims
            ],
            'avg_pending_days': round(avg_pending_days, 1),
            'total_pending': pending_claims.count()
        }
    
    @staticmethod
    def provider_performance_report():
        """Performance metrics by insurance provider"""
        verifications = InsuranceVerification.objects.filter(
            status='ACTIVE'
        )
        
        report = []
        for verification in verifications:
            claims = InsuranceClaim.objects.filter(
                insurance_verification=verification
            )
            
            if claims.exists():
                approved = claims.filter(status='APPROVED').count()
                denied = claims.filter(status__in=['DENIED', 'REJECTED']).count()
                total = claims.count()
                
                report.append({
                    'provider': verification.provider_name,
                    'policy_count': InsuranceVerification.objects.filter(
                        provider_name=verification.provider_name
                    ).count(),
                    'total_claims': total,
                    'approved_claims': approved,
                    'denied_claims': denied,
                    'approval_rate': round((approved / total * 100) if total > 0 else 0, 2),
                    'avg_claim_value': float(claims.aggregate(avg=Sum('claimed_amount'))['avg'] or 0),
                    'total_claimed': float(claims.aggregate(total=Sum('claimed_amount'))['total'] or 0),
                    'total_approved': float(claims.aggregate(total=Sum('approved_amount'))['total'] or 0)
                })
        
        return sorted(report, key=lambda x: x['total_claims'], reverse=True)
    
    @staticmethod
    def refund_summary():
        """Refund processing summary"""
        refunds = Refund.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        return {
            'by_status': [
                {
                    'status': r['status'],
                    'count': r['count'],
                    'total_amount': float(r['total_amount'] or 0)
                }
                for r in refunds
            ],
            'pending_approval': Refund.objects.filter(
                status='PENDING_APPROVAL'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            'total_refunded': Refund.objects.filter(
                status='COMPLETED'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        }
