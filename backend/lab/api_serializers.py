"""Serializers for lab-related API endpoints"""
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from .models import TestTemplate, TestBooking, TestResult, TestResultItem, TestRecommendation, TestSchedule


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
    
    class Meta:
        model = TestResult
        fields = [
            'id',
            'booking',
            'booking_info',
            'status',
            'notes',
            'pdf_file',
            'is_released',
            'has_critical_values',
            'items',
            'filled_at',
        ]
        read_only_fields = ['id', 'filled_at', 'items']


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
