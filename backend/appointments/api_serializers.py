"""Serializers for appointments and clinical-related API endpoints"""
from rest_framework import serializers
from appointments.models import Appointment, MedicalReportAnalysis, TriageAssessment
from clinical.models import Doctor, Specialization


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'icon']
        read_only_fields = ['id']


class DoctorSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    specialization = SpecializationSerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = [
            'id',
            'user',
            'specialization',
            'consultation_fee',
            'bio',
            'experience_years',
            'is_available',
            'photo',
            'phone',
        ]
        read_only_fields = ['id']
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    doctor_details = DoctorSerializer(source='doctor', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'patient_name',
            'doctor',
            'doctor_name',
            'doctor_details',
            'date',
            'start_time',
            'end_time',
            'status',
            'notes',
            'pdf_file',
            'qr_code',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'qr_code', 'pdf_file', 'created_at', 'updated_at']
    
    def get_patient_name(self, obj):
        return obj.patient.full_name
    
    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.first_name} {obj.doctor.user.last_name}"


class MedicalReportAnalysisSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)

    class Meta:
        model = MedicalReportAnalysis
        fields = [
            'id',
            'patient',
            'patient_name',
            'title',
            'report_file',
            'report_type',
            'risk_level',
            'ai_summary',
            'abnormal_flags',
            'recommendations',
            'created_at',
        ]


class TriageAssessmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)

    class Meta:
        model = TriageAssessment
        fields = [
            'id',
            'patient',
            'patient_name',
            'symptoms',
            'duration_days',
            'pain_level',
            'has_fever',
            'has_breathing_issue',
            'has_chest_pain',
            'has_heavy_bleeding',
            'had_fainting_episode',
            'priority',
            'priority_score',
            'ai_summary',
            'recommended_action',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'patient_name',
            'priority',
            'priority_score',
            'ai_summary',
            'recommended_action',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'patient_name',
            'report_type',
            'risk_level',
            'ai_summary',
            'abnormal_flags',
            'recommendations',
            'created_at',
        ]
