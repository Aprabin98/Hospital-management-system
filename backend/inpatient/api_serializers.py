from rest_framework import serializers

from .models import (
    InpatientStay,
    ProgressNote,
    DailyRound,
    DischargePackage,
    DischargeMedicationReconciliation,
    MedicationAdministrationRecord,
    ProcedureSchedule,
)


class InpatientStaySerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    attending_doctor_name = serializers.SerializerMethodField()
    bed_label = serializers.SerializerMethodField()
    length_of_stay_days = serializers.SerializerMethodField()

    class Meta:
        model = InpatientStay
        fields = [
            'id',
            'patient',
            'patient_name',
            'attending_doctor',
            'attending_doctor_name',
            'admission_request',
            'room_assignment',
            'bed_label',
            'admission_appointment',
            'primary_diagnosis',
            'admission_reason',
            'care_notes',
            'status',
            'expected_discharge_date',
            'actual_discharge_date',
            'admitted_by',
            'admission_datetime',
            'updated_at',
            'length_of_stay_days',
        ]

    def get_patient_name(self, obj):
        return obj.patient.full_name if obj.patient_id else ''

    def get_attending_doctor_name(self, obj):
        if not obj.attending_doctor_id:
            return ''
        user = obj.attending_doctor.user
        return f"Dr. {user.first_name} {user.last_name}".strip()

    def get_bed_label(self, obj):
        if not obj.room_assignment_id or not obj.room_assignment.bed_id:
            return ''
        bed = obj.room_assignment.bed
        return f"{bed.room.room_number} / Bed {bed.bed_number}"

    def get_length_of_stay_days(self, obj):
        return obj.length_of_stay_days


class ProgressNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ProgressNote
        fields = [
            'id',
            'inpatient_stay',
            'author',
            'author_name',
            'note_type',
            'clinical_findings',
            'assessment',
            'plan',
            'created_at',
        ]

    def get_author_name(self, obj):
        if not obj.author_id:
            return 'System'
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.email


class DailyRoundSerializer(serializers.ModelSerializer):
    round_assessor_name = serializers.SerializerMethodField()
    signed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DailyRound
        fields = [
            'id',
            'inpatient_stay',
            'round_date',
            'round_assessor',
            'round_assessor_name',
            'round_notes',
            'vital_assessment',
            'current_status',
            'orders',
            'is_signed',
            'signed_by',
            'signed_by_name',
            'signed_at',
            'created_at',
        ]

    def get_round_assessor_name(self, obj):
        if not obj.round_assessor_id:
            return 'System'
        return f"{obj.round_assessor.first_name} {obj.round_assessor.last_name}".strip() or obj.round_assessor.email

    def get_signed_by_name(self, obj):
        if not obj.signed_by_id:
            return ''
        return f"{obj.signed_by.first_name} {obj.signed_by.last_name}".strip() or obj.signed_by.email


class MedicationAdministrationRecordSerializer(serializers.ModelSerializer):
    administered_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MedicationAdministrationRecord
        fields = [
            'id',
            'inpatient_stay',
            'prescription_item',
            'medication_name',
            'dose_given',
            'route',
            'scheduled_datetime',
            'administered_datetime',
            'status',
            'administered_by',
            'administered_by_name',
            'reason_not_given',
            'deviations',
            'notes',
            'created_at',
        ]

    def get_administered_by_name(self, obj):
        if not obj.administered_by_id:
            return ''
        return f"{obj.administered_by.first_name} {obj.administered_by.last_name}".strip() or obj.administered_by.email


class ProcedureScheduleSerializer(serializers.ModelSerializer):
    surgeon_name = serializers.SerializerMethodField()

    class Meta:
        model = ProcedureSchedule
        fields = [
            'id',
            'inpatient_stay',
            'procedure_name',
            'scheduled_datetime',
            'ot_room_number',
            'surgeon',
            'surgeon_name',
            'indication',
            'status',
            'actual_start_time',
            'actual_end_time',
            'notes',
            'created_at',
        ]

    def get_surgeon_name(self, obj):
        if not obj.surgeon_id:
            return ''
        user = obj.surgeon.user
        return f"Dr. {user.first_name} {user.last_name}".strip()


class DischargePackageSerializer(serializers.ModelSerializer):
    doctor_signed_off_by_name = serializers.SerializerMethodField()
    patient_acknowledged_by_name = serializers.SerializerMethodField()
    checklist_complete = serializers.SerializerMethodField()

    class Meta:
        model = DischargePackage
        fields = [
            'id',
            'inpatient_stay',
            'discharge_date',
            'discharge_summary',
            'discharge_diagnoses',
            'discharge_instructions',
            'follow_up_date',
            'follow_up_provider',
            'follow_up_specialty',
            'doctor_signed_off_by',
            'doctor_signed_off_by_name',
            'doctor_signed_off_at',
            'patient_acknowledged_by',
            'patient_acknowledged_by_name',
            'patient_acknowledged_at',
            'nursing_clearance',
            'pharmacy_clearance',
            'billing_clearance',
            'final_approved',
            'checklist_complete',
            'created_at',
            'updated_at',
        ]

    def get_doctor_signed_off_by_name(self, obj):
        if not obj.doctor_signed_off_by_id:
            return ''
        user = obj.doctor_signed_off_by
        return f"{user.first_name} {user.last_name}".strip() or user.email

    def get_patient_acknowledged_by_name(self, obj):
        if not obj.patient_acknowledged_by_id:
            return ''
        user = obj.patient_acknowledged_by
        return f"{user.first_name} {user.last_name}".strip() or user.email

    def get_checklist_complete(self, obj):
        return obj.checklist_complete


class DischargeMedicationReconciliationSerializer(serializers.ModelSerializer):
    reconciled_by_name = serializers.SerializerMethodField()
    is_complete = serializers.SerializerMethodField()

    class Meta:
        model = DischargeMedicationReconciliation
        fields = [
            'id',
            'inpatient_stay',
            'home_medications',
            'discharge_medications',
            'reconciliation_notes',
            'interactions_checked',
            'allergies_reviewed',
            'patient_counseled',
            'reconciled_by',
            'reconciled_by_name',
            'reconciled_at',
            'is_complete',
            'created_at',
            'updated_at',
        ]

    def get_reconciled_by_name(self, obj):
        if not obj.reconciled_by_id:
            return ''
        user = obj.reconciled_by
        return f"{user.first_name} {user.last_name}".strip() or user.email

    def get_is_complete(self, obj):
        return obj.is_complete
