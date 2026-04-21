from django.contrib import admin

from .models import (
    DailyRound,
    DischargePackage,
    InpatientStay,
    MedicationAdministrationRecord,
    ProcedureSchedule,
    ProgressNote,
)


@admin.register(InpatientStay)
class InpatientStayAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'attending_doctor', 'status', 'admission_datetime', 'expected_discharge_date', 'actual_discharge_date')
    list_filter = ('status', 'admission_datetime', 'expected_discharge_date')
    search_fields = ('patient__full_name', 'patient__user__email', 'primary_diagnosis')
    readonly_fields = ('admission_datetime', 'updated_at')


@admin.register(ProgressNote)
class ProgressNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'inpatient_stay', 'note_type', 'author', 'created_at')
    list_filter = ('note_type', 'created_at')
    search_fields = ('inpatient_stay__patient__full_name', 'assessment', 'plan')
    readonly_fields = ('created_at',)


@admin.register(DailyRound)
class DailyRoundAdmin(admin.ModelAdmin):
    list_display = ('id', 'inpatient_stay', 'round_date', 'round_assessor', 'is_signed', 'signed_at')
    list_filter = ('round_date', 'is_signed')
    search_fields = ('inpatient_stay__patient__full_name', 'round_notes', 'orders')
    readonly_fields = ('created_at',)


@admin.register(MedicationAdministrationRecord)
class MedicationAdministrationRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'inpatient_stay', 'medication_name', 'status', 'scheduled_datetime', 'administered_datetime', 'administered_by')
    list_filter = ('status', 'scheduled_datetime')
    search_fields = ('inpatient_stay__patient__full_name', 'medication_name', 'dose_given')
    readonly_fields = ('created_at',)


@admin.register(ProcedureSchedule)
class ProcedureScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'inpatient_stay', 'procedure_name', 'scheduled_datetime', 'status', 'surgeon')
    list_filter = ('status', 'scheduled_datetime')
    search_fields = ('inpatient_stay__patient__full_name', 'procedure_name', 'ot_room_number')
    readonly_fields = ('created_at',)


@admin.register(DischargePackage)
class DischargePackageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'inpatient_stay',
        'discharge_date',
        'follow_up_date',
        'doctor_signed_off_at',
        'final_approved',
    )
    list_filter = ('final_approved', 'discharge_date', 'follow_up_date')
    search_fields = ('inpatient_stay__patient__full_name', 'discharge_summary', 'discharge_diagnoses')
    readonly_fields = ('created_at', 'updated_at')
