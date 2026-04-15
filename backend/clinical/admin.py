from django.contrib import admin
from .models import Specialization, Doctor, Shift, DoctorSchedule, DoctorLeave


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