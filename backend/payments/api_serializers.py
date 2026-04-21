"""Serializers for Payment APIs"""
from rest_framework import serializers
from .models import (
    Payment, Refund, InsurancePreAuth, Invoice, InvoiceLineItem,
    InsuranceClaim, ClaimAuditLog, DenialRework, InsuranceVerification
)


class PaymentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(
        source='patient.full_name',
        read_only=True
    )
    patient_email = serializers.CharField(
        source='patient.user.email',
        read_only=True
    )
    doctor_name = serializers.CharField(
        source='doctor.user.username',
        read_only=True,
        allow_null=True
    )
    appointment_id = serializers.IntegerField(
        source='appointment.id',
        read_only=True,
        allow_null=True
    )
    lab_booking_id = serializers.IntegerField(
        source='lab_booking.id',
        read_only=True,
        allow_null=True
    )
    lab_booking_name = serializers.CharField(
        source='lab_booking.template.name',
        read_only=True,
        allow_null=True
    )
    amount_remaining = serializers.SerializerMethodField()
    has_refund_request = serializers.SerializerMethodField()
    refund_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_type', 'patient', 'patient_name', 'patient_email',
            'doctor_name', 'amount', 'amount_paid', 'amount_remaining',
            'status', 'payment_method', 'paid_at', 'due_date', 'notes',
            'appointment_id', 'lab_booking_id', 'lab_booking_name',
            'is_overdue', 'overdue_days', 'has_refund_request', 'refund_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'patient', 'created_at', 'updated_at', 'is_overdue', 'overdue_days'
        ]
    
    def get_amount_remaining(self, obj):
        """Calculate remaining amount to be paid"""
        return float(obj.amount - obj.amount_paid)

    def get_has_refund_request(self, obj):
        return hasattr(obj, 'refund')

    def get_refund_status(self, obj):
        refund = getattr(obj, 'refund', None)
        return refund.status if refund else None


class RefundSerializer(serializers.ModelSerializer):
    payment_id = serializers.IntegerField(
        source='payment.id',
        read_only=True
    )
    payment_amount = serializers.DecimalField(
        source='payment.amount',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Refund
        fields = [
            'id', 'payment_id', 'payment_amount', 'reason', 'status',
            'refunded_at', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'refunded_at', 'created_at']


# ===============================================
# PHASE 7: FINANCE & INSURANCE SERIALIZERS
# ===============================================

class InsurancePreAuthSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    insurance_provider = serializers.CharField(source='insurance_verification.provider_name', read_only=True)
    
    class Meta:
        model = InsurancePreAuth
        fields = [
            'id', 'patient', 'patient_name', 'insurance_provider',
            'treatment_code', 'estimated_amount', 'approved_amount',
            'status', 'pre_auth_number', 'valid_from', 'valid_until',
            'requested_at', 'approved_at', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'pre_auth_number', 'requested_at', 'created_at']


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = [
            'id', 'description', 'quantity', 'unit_price', 'total',
            'appointment', 'lab_booking'
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_type', 'patient', 'patient_name',
            'appointment', 'subtotal', 'tax_amount', 'discount_amount',
            'total_amount', 'amount_paid', 'status', 'due_date', 'issued_date',
            'insurance_verification', 'insurance_amount', 'patient_amount',
            'line_items', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'created_at', 'updated_at'
        ]


class ClaimAuditLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = ClaimAuditLog
        fields = [
            'id', 'claim', 'old_status', 'new_status', 'changed_by',
            'changed_by_name', 'change_reason', 'notes', 'changed_at'
        ]
        read_only_fields = ['id', 'changed_at']


class InsuranceClaimSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    insurance_provider = serializers.CharField(source='insurance_verification.provider_name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    audit_logs = ClaimAuditLogSerializer(many=True, read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = InsuranceClaim
        fields = [
            'id', 'claim_number', 'invoice', 'invoice_number', 'patient',
            'patient_name', 'insurance_verification', 'insurance_provider',
            'claimed_amount', 'approved_amount', 'reduction_reason',
            'status', 'submitted_at', 'received_at', 'approved_at',
            'days_pending', 'submitted_by', 'submitted_by_name',
            'submission_reference', 'submission_notes', 'audit_logs',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'claim_number', 'created_at', 'updated_at'
        ]


class DenialReworkSerializer(serializers.ModelSerializer):
    claim_number = serializers.CharField(source='claim.claim_number', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    patient_name = serializers.CharField(source='claim.patient.full_name', read_only=True)
    
    class Meta:
        model = DenialRework
        fields = [
            'id', 'claim', 'claim_number', 'patient_name',
            'original_denial_reason', 'status', 'assigned_to',
            'assigned_to_name', 'correction_notes', 'resubmit_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'claim_number', 'created_at']


class InsuranceVerificationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = InsuranceVerification
        fields = [
            'id', 'patient', 'patient_name', 'provider_name', 'policy_number',
            'plan_name', 'coverage_percent', 'valid_until', 'status',
            'verified_by', 'verified_by_name', 'verified_at',
            'verification_notes', 'external_reference', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verified_at', 'created_at']
