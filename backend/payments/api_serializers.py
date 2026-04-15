"""Serializers for Payment APIs"""
from rest_framework import serializers
from .models import Payment, Refund


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
