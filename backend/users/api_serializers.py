"""Serializers for user-related API endpoints"""
from rest_framework import serializers
from .models import User, PatientProfile, PatientHealthRecord, PatientVitalLog
from clinical.models import Doctor, Specialization


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'role']
        read_only_fields = ['id']


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PatientProfile
        fields = [
            'id',
            'user',
            'full_name',
            'phone',
            'gender',
            'date_of_birth',
            'blood_group',
            'height',
            'weight',
            'image',
            'address',
            'emergency_contact',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PatientHealthRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientHealthRecord
        fields = [
            'id',
            'patient',
            'allergies',
            'chronic_conditions',
            'surgical_history',
            'family_history',
            'current_medications',
            'immunization_notes',
            'emergency_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PatientVitalLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientVitalLog
        fields = [
            'id',
            'patient',
            'blood_pressure',
            'pulse',
            'temperature_c',
            'respiratory_rate',
            'oxygen_saturation',
            'weight_kg',
            'height_cm',
            'notes',
            'recorded_by',
            'recorded_at',
        ]
        read_only_fields = ['id', 'recorded_at']


class DoctorProfileSerializer(serializers.ModelSerializer):
    specialization_name = serializers.CharField(source='specialization.name', read_only=True)
    specialization = serializers.PrimaryKeyRelatedField(
        queryset=Specialization.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Doctor
        fields = [
            'id',
            'specialization',
            'specialization_name',
            'consultation_fee',
            'experience_years',
            'phone',
            'bio',
            'photo',
            'is_available',
        ]
        read_only_fields = ['id']
