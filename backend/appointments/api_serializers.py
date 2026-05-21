"""Serializers for appointments and clinical-related API endpoints"""
from rest_framework import serializers
from appointments.models import (
    Appointment,
    MedicalReportAnalysis,
    TriageAssessment,
    PatientMatch,
    Queue,
    NursingNote,
    NursingTask,
)
from clinical.models import Doctor, Specialization


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'icon']
        read_only_fields = ['id']


class DoctorSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    specialization = SpecializationSerializer(read_only=True)
    photo_url = serializers.SerializerMethodField()
    
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
            'photo_url',
            'phone',
        ]
        read_only_fields = ['id']
    
    def get_user(self, obj):
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'display_name': full_name or obj.user.username or obj.user.email,
        }

    def get_photo_url(self, obj):
        if not obj.photo:
            return ''

        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.photo.url)
        return obj.photo.url


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    doctor_details = DoctorSerializer(source='doctor', read_only=True)
    payment_id = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    payment_amount = serializers.SerializerMethodField()
    
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
            'payment_id',
            'payment_status',
            'payment_method',
            'payment_amount',
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

    def _get_appointment_payment(self, obj):
        return obj.payments.order_by('-created_at').first()

    def get_payment_id(self, obj):
        payment = self._get_appointment_payment(obj)
        return payment.id if payment else None

    def get_payment_status(self, obj):
        payment = self._get_appointment_payment(obj)
        return payment.status if payment else None

    def get_payment_method(self, obj):
        payment = self._get_appointment_payment(obj)
        return payment.payment_method if payment else None

    def get_payment_amount(self, obj):
        payment = self._get_appointment_payment(obj)
        return float(payment.amount) if payment else None


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


class PatientMatchSerializer(serializers.ModelSerializer):
    new_patient_name = serializers.CharField(source='new_patient.full_name', read_only=True)
    existing_patient_name = serializers.CharField(source='existing_patient.full_name', read_only=True)
    
    class Meta:
        model = PatientMatch
        fields = [
            'id',
            'new_patient',
            'new_patient_name',
            'existing_patient',
            'existing_patient_name',
            'match_type',
            'confidence_score',
            'reviewed_by',
            'reviewed_at',
            'is_duplicate',
            'created_at',
        ]
        read_only_fields = ['id', 'new_patient_name', 'existing_patient_name', 'created_at']


class QueueSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    wait_time_minutes = serializers.IntegerField(read_only=True)
    consultation_duration_minutes = serializers.IntegerField(read_only=True)
    triage_priority = serializers.CharField(source='triage_assessment.priority', read_only=True, allow_null=True)
    
    class Meta:
        model = Queue
        fields = [
            'id',
            'patient',
            'patient_name',
            'doctor',
            'doctor_name',
            'appointment',
            'status',
            'source',
            'priority',
            'queued_at',
            'called_at',
            'consultation_start',
            'consultation_end',
            'wait_time_minutes',
            'consultation_duration_minutes',
            'triage_assessment',
            'triage_priority',
            'notes',
            'no_show_reason',
            'rebooking_attempted',
            'rebooking_contact_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'patient_name',
            'doctor_name',
            'wait_time_minutes',
            'consultation_duration_minutes',
            'triage_priority',
            'created_at',
        ]

    def get_patient_name(self, obj):
        full_name = (obj.patient.full_name or '').strip()
        if full_name:
            return full_name
        user = getattr(obj.patient, 'user', None)
        if user:
            user_full_name = f"{user.first_name} {user.last_name}".strip()
            return user_full_name or user.username or user.email
        return f'Patient #{obj.patient_id}'

    def get_doctor_name(self, obj):
        full_name = f"{obj.doctor.user.first_name} {obj.doctor.user.last_name}".strip()
        return f"Dr. {full_name or obj.doctor.user.username or obj.doctor.user.email}"
    
    def get_doctor_name(self, obj):
            full_name = f"{obj.doctor.user.first_name} {obj.doctor.user.last_name}".strip()
            return f"Dr. {full_name or obj.doctor.user.username or obj.doctor.user.email}"


class NursingNoteSerializer(serializers.ModelSerializer):
    nurse_name = serializers.SerializerMethodField()
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)

    class Meta:
        model = NursingNote
        fields = [
            'id',
            'appointment',
            'patient',
            'patient_name',
            'nurse',
            'nurse_name',
            'triage_tag',
            'note',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'patient_name', 'nurse_name', 'created_at', 'updated_at']

    def get_nurse_name(self, obj):
        if not obj.nurse:
            return None
        full_name = f"{obj.nurse.first_name} {obj.nurse.last_name}".strip()
        return full_name or obj.nurse.username or obj.nurse.email


class NursingTaskSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = NursingTask
        fields = [
            'id',
            'appointment',
            'patient',
            'patient_name',
            'title',
            'details',
            'status',
            'due_at',
            'completed_at',
            'assigned_to',
            'assigned_to_name',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'patient_name',
            'assigned_to_name',
            'created_by_name',
            'completed_at',
            'created_at',
            'updated_at',
        ]

    def get_assigned_to_name(self, obj):
        if not obj.assigned_to:
            return None
        full_name = f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip()
        return full_name or obj.assigned_to.username or obj.assigned_to.email

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None
        full_name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return full_name or obj.created_by.username or obj.created_by.email
