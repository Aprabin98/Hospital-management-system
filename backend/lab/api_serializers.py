"""Serializers for lab-related API endpoints"""
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from .models import (
    TestTemplate, TestBooking, TestResult, TestResultItem, TestRecommendation, TestSchedule,
    LabSample, QCLog, CriticalValueAcknowledgment
)


class TestScheduleSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = TestSchedule
        fields = ['id', 'day', 'day_display', 'start_time', 'end_time', 'is_active']
        read_only_fields = ['id', 'day_display']


class TestTemplateSerializer(serializers.ModelSerializer):
    schedules = serializers.SerializerMethodField()
    available_dates = serializers.SerializerMethodField()

    class Meta:
        model = TestTemplate
        fields = [
            'id',
            'name',
            'description',
            'preparation',
            'price',
            'duration_minutes',
            'is_available',
            'schedules',
            'available_dates',
        ]
        read_only_fields = ['id']

    def get_schedules(self, obj):
        schedules = obj.schedules.filter(is_active=True).order_by('day', 'start_time')
        return TestScheduleSerializer(schedules, many=True).data

    def get_available_dates(self, obj):
        schedules = obj.schedules.filter(is_active=True).order_by('day', 'start_time')
        today = timezone.localdate()
        upcoming = []

        for schedule in schedules:
            target_weekday = self._weekday_from_code(schedule.day)
            if target_weekday is None:
                continue

            days_ahead = (target_weekday - today.weekday()) % 7
            next_date = today + timedelta(days=days_ahead)
            upcoming.append({
                'day': schedule.get_day_display(),
                'date': next_date.isoformat(),
                'start_time': schedule.start_time.strftime('%H:%M'),
                'end_time': schedule.end_time.strftime('%H:%M'),
            })

        return upcoming

    def _weekday_from_code(self, code):
        mapping = {
            'MON': 0,
            'TUE': 1,
            'WED': 2,
            'THU': 3,
            'FRI': 4,
            'SAT': 5,
            'SUN': 6,
        }
        return mapping.get(code)


class TestBookingSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    
    class Meta:
        model = TestBooking
        fields = [
            'id',
            'patient',
            'patient_name',
            'template',
            'template_name',
            'date',
            'status',
            'payment_status',
            'amount',
            'specimen_id',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'specimen_id']


class TestResultItemSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(source='field.field_name', read_only=True)
    unit = serializers.CharField(source='field.unit', read_only=True)
    
    class Meta:
        model = TestResultItem
        fields = ['id', 'field', 'field_name', 'unit', 'value', 'status', 'is_critical']
        read_only_fields = ['id']


class TestResultSerializer(serializers.ModelSerializer):
    booking_info = TestBookingSerializer(source='booking', read_only=True)
    items = TestResultItemSerializer(many=True, read_only=True)
    pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TestResult
        fields = [
            'id',
            'booking',
            'booking_info',
            'status',
            'notes',
            'pdf_file',
            'pdf_url',
            'is_released',
            'has_critical_values',
            'items',
            'filled_at',
        ]
        read_only_fields = ['id', 'filled_at', 'items']

    def get_pdf_url(self, obj):
        if not obj.pdf_file:
            return ''

        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.pdf_file.url)
        return obj.pdf_file.url


class TestRecommendationSerializer(serializers.ModelSerializer):
    test_name = serializers.CharField(source='template.name', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    recommended_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TestRecommendation
        fields = [
            'id',
            'patient',
            'patient_name',
            'template',
            'test_name',
            'recommended_by',
            'recommended_by_name',
            'doctor',
            'reason',
            'priority',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'patient_name', 'test_name', 'recommended_by_name']

    def get_recommended_by_name(self, obj):
        if not obj.recommended_by:
            return None
        full_name = f"{obj.recommended_by.first_name} {obj.recommended_by.last_name}".strip()
        return full_name or obj.recommended_by.username or obj.recommended_by.email


# ==================== PHASE 4 Serializers ====================

class LabSampleSerializer(serializers.ModelSerializer):
    """Serializer for LabSample model with tracking metadata."""
    result_id = serializers.IntegerField(source='result.id', read_only=True)
    collected_by_name = serializers.SerializerMethodField()
    processed_by_name = serializers.SerializerMethodField()
    validated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LabSample
        fields = [
            'id',
            'result_id',
            'barcode_id',
            'status',
            'collected_by',
            'collected_by_name',
            'collected_at',
            'processed_by',
            'processed_by_name',
            'processed_at',
            'validated_by',
            'validated_by_name',
            'validated_at',
            'rejection_reason',
            'recollect_reason',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'collected_by_name', 'processed_by_name', 'validated_by_name', 'result_id']

    def get_collected_by_name(self, obj):
        if not obj.collected_by:
            return None
        return f"{obj.collected_by.first_name} {obj.collected_by.last_name}".strip() or obj.collected_by.email

    def get_processed_by_name(self, obj):
        if not obj.processed_by:
            return None
        return f"{obj.processed_by.first_name} {obj.processed_by.last_name}".strip() or obj.processed_by.email

    def get_validated_by_name(self, obj):
        if not obj.validated_by:
            return None
        return f"{obj.validated_by.first_name} {obj.validated_by.last_name}".strip() or obj.validated_by.email


class QCLogSerializer(serializers.ModelSerializer):
    """Serializer for QCLog model."""
    performed_by_name = serializers.SerializerMethodField()
    test_name = serializers.CharField(source='test_template.name', read_only=True)

    class Meta:
        model = QCLog
        fields = [
            'id',
            'sample',
            'qc_type',
            'test_template',
            'test_name',
            'performed_by',
            'performed_by_name',
            'result',
            'details',
            'reference_value',
            'actual_value',
            'deviation',
            'performed_at',
        ]
        read_only_fields = ['id', 'performed_at', 'performed_by_name', 'test_name']

    def get_performed_by_name(self, obj):
        if not obj.performed_by:
            return None
        return f"{obj.performed_by.first_name} {obj.performed_by.last_name}".strip() or obj.performed_by.email


class CriticalValueAcknowledgmentSerializer(serializers.ModelSerializer):
    """Serializer for CriticalValueAcknowledgment model."""
    acknowledged_by_name = serializers.SerializerMethodField()
    escalated_to_name = serializers.SerializerMethodField()
    result_details = serializers.SerializerMethodField()

    class Meta:
        model = CriticalValueAcknowledgment
        fields = [
            'id',
            'result',
            'result_details',
            'is_critical',
            'urgency',
            'critical_fields',
            'notification_sent_at',
            'notification_method',
            'acknowledged_by',
            'acknowledged_by_name',
            'acknowledged_at',
            'acknowledgment_notes',
            'escalated_to',
            'escalated_to_name',
            'escalated_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'acknowledged_by_name', 'escalated_to_name', 'result_details']

    def get_acknowledged_by_name(self, obj):
        if not obj.acknowledged_by:
            return None
        doctor = obj.acknowledged_by
        return f"Dr. {doctor.user.first_name} {doctor.user.last_name}".strip()

    def get_escalated_to_name(self, obj):
        if not obj.escalated_to:
            return None
        return f"{obj.escalated_to.first_name} {obj.escalated_to.last_name}".strip() or obj.escalated_to.email

    def get_result_details(self, obj):
        """Include basic result info for context."""
        if not obj.result:
            return None
        return {
            'id': obj.result.id,
            'booking_id': obj.result.booking.id,
            'status': obj.result.status,
            'has_critical_values': obj.result.has_critical_values,
        }
