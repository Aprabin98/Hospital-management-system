from rest_framework import serializers

from .models import EmergencyClinicalNote, EmergencyEncounter, EmergencyTriage


class EmergencyEncounterSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='assigned_doctor.user.get_full_name', read_only=True)

    class Meta:
        model = EmergencyEncounter
        fields = [
            'id',
            'patient',
            'patient_name',
            'assigned_doctor',
            'doctor_name',
            'arrival_mode',
            'triage_level',
            'severity_priority',
            'status',
            'chief_complaint',
            'stabilization_notes',
            'disposition_notes',
            'arrived_at',
            'triaged_at',
            'closed_at',
            'created_by',
            'updated_at',
        ]
        read_only_fields = ['created_by', 'arrived_at', 'updated_at']


class EmergencyTriageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyTriage
        fields = [
            'id',
            'encounter',
            'pulse',
            'systolic_bp',
            'diastolic_bp',
            'temperature_c',
            'respiratory_rate',
            'oxygen_saturation',
            'pain_score',
            'triage_notes',
            'triaged_by',
            'created_at',
        ]
        read_only_fields = ['triaged_by', 'created_at']


class EmergencyClinicalNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='authored_by.get_full_name', read_only=True)

    class Meta:
        model = EmergencyClinicalNote
        fields = [
            'id',
            'encounter',
            'note_type',
            'content',
            'authored_by',
            'author_name',
            'created_at',
        ]
        read_only_fields = ['authored_by', 'created_at']
