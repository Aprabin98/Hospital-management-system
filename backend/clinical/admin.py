from django.contrib import admin
from .models import Specialization, Doctor, Shift, DoctorSchedule, DoctorLeave, PatientVisit, PatientDocument


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'consultation_fee', 'experience_years', 'is_available']
    list_filter = ['specialization', 'is_available']
    search_fields = ['user__username', 'user__email']


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time', 'slot_duration']


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day', 'shift', 'is_active']
    list_filter = ['day', 'shift', 'is_active']
    search_fields = ['doctor__user__username']


@admin.register(DoctorLeave)
class DoctorLeaveAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'reason']
    list_filter = ['date']
    search_fields = ['doctor__user__username']


@admin.register(PatientVisit)
class PatientVisitAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'ai_risk_level', 'follow_up_date', 'follow_up_completed', 'visit_date']
    list_filter = ['ai_risk_level', 'follow_up_completed', 'follow_up_date', 'visit_date']
    search_fields = ['patient__full_name', 'symptoms', 'diagnosis']


@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'title', 'document_type', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['patient__full_name', 'title']
