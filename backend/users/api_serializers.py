"""Serializers for user-related API endpoints"""
from rest_framework import serializers
from .models import User, PatientProfile, PatientHealthRecord, PatientVitalLog, PatientAllergy
from clinical.models import Doctor, Specialization


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'role']
        read_only_fields = ['id']


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientProfile
        fields = [
            'id',
            'user',
            'display_name',
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
        read_only_fields = ['id', 'display_name', 'created_at', 'updated_at']

    def get_display_name(self, obj):
        full_name = (obj.full_name or '').strip()
        if full_name:
            return full_name
        user = getattr(obj, 'user', None)
        if user:
            user_full_name = f"{user.first_name} {user.last_name}".strip()
            return user_full_name or user.username or user.email
        return ''


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


class PatientAllergySerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientAllergy
        fields = [
            'id',
            'patient',
            'allergen',
            'reaction',
            'severity',
            'status',
            'diagnosed_on',
            'notes',
            'recorded_by',
            'recorded_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'recorded_by_name', 'created_at', 'updated_at']

    def get_recorded_by_name(self, obj):
        if not obj.recorded_by:
            return ''
        name = f"{obj.recorded_by.first_name} {obj.recorded_by.last_name}".strip()
        return name or obj.recorded_by.email


class DoctorProfileSerializer(serializers.ModelSerializer):
    specialization_name = serializers.CharField(source='specialization.name', read_only=True)
    doctor_name = serializers.SerializerMethodField()
    doctor_email = serializers.EmailField(source='user.email', read_only=True)
    photo_url = serializers.SerializerMethodField()
    specialization = serializers.PrimaryKeyRelatedField(
        queryset=Specialization.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Doctor
        fields = [
            'id',
            'doctor_name',
            'doctor_email',
            'specialization',
            'specialization_name',
            'consultation_fee',
            'experience_years',
            'phone',
            'bio',
            'photo',
            'photo_url',
            'is_available',
        ]
        read_only_fields = ['id']

    def get_doctor_name(self, obj):
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full_name or obj.user.username or obj.user.email

    def get_photo_url(self, obj):
        if not obj.photo:
            return ''

        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.photo.url)
        return obj.photo.url
