"""Serializers for prescription-related API endpoints"""
from rest_framework import serializers
from .models import Prescription, PrescriptionItem


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = ['id', 'medicine_name', 'dosage', 'frequency', 'duration', 'timing', 'instructions']
        read_only_fields = ['id']


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True)
    appointment_date = serializers.DateField(source='appointment.date', read_only=True)
    items = PrescriptionItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'id',
            'patient',
            'patient_name',
            'doctor',
            'doctor_name',
            'appointment',
            'appointment_date',
            'notes',
            'advice',
            'follow_up_date',
            'pdf_file',
            'refill_status',
            'total_refills_allowed',
            'refills_remaining',
            'expiry_date',
            'is_expired',
            'items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'items']
