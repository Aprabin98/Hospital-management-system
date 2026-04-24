from rest_framework import serializers

from .models import OTSchedule, ProcedureNote, PostOpNote


class OTScheduleSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    surgeon_name = serializers.CharField(source='surgeon.user.username', read_only=True)
    anesthetist_name = serializers.CharField(source='anesthetist.user.username', read_only=True)

    class Meta:
        model = OTSchedule
        fields = [
            'id',
            'patient',
            'patient_name',
            'inpatient_stay',
            'surgeon',
            'surgeon_name',
            'anesthetist',
            'anesthetist_name',
            'procedure_name',
            'ot_room',
            'scheduled_start',
            'scheduled_end',
            'status',
            'pre_op_checklist',
            'surgery_billing_amount',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class ProcedureNoteSerializer(serializers.ModelSerializer):
    signed_by_name = serializers.CharField(source='signed_by.username', read_only=True)

    class Meta:
        model = ProcedureNote
        fields = [
            'id',
            'schedule',
            'procedure_steps',
            'findings',
            'complications',
            'anesthesia_notes',
            'signed_by',
            'signed_by_name',
            'signed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['schedule', 'signed_by', 'signed_at', 'created_at', 'updated_at']


class PostOpNoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = PostOpNote
        fields = [
            'id',
            'schedule',
            'recovery_status',
            'pain_score',
            'notes',
            'created_by',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = ['schedule', 'created_by', 'created_at']
