from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PatientProfile, LoginAttempt
from .models import TwoFactorCode
from .models import PatientHealthRecord, PatientVitalLog
from .models import PatientAllergy


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Role & Status', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Token', {'fields': ('activation_token',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'role', 'password1', 'password2', 'is_active'),
        }),
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'phone', 'gender', 'blood_group']
    search_fields = ['full_name', 'user__email']
    list_filter = ['gender', 'blood_group']


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['identifier', 'failed_count', 'last_ip', 'last_attempt', 'locked_until']
    search_fields = ['identifier', 'last_ip']


@admin.register(TwoFactorCode)
class TwoFactorCodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'expires_at', 'attempts', 'is_used', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']


@admin.register(PatientHealthRecord)
class PatientHealthRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'updated_by', 'updated_at']
    search_fields = ['patient__full_name', 'patient__user__email']
    ordering = ['-updated_at']


@admin.register(PatientVitalLog)
class PatientVitalLogAdmin(admin.ModelAdmin):
    list_display = ['patient', 'blood_pressure', 'pulse', 'temperature_c', 'recorded_by', 'recorded_at']
    search_fields = ['patient__full_name', 'patient__user__email']
    ordering = ['-recorded_at']


@admin.register(PatientAllergy)
class PatientAllergyAdmin(admin.ModelAdmin):
    list_display = ['patient', 'allergen', 'severity', 'status', 'recorded_by', 'updated_at']
    search_fields = ['patient__full_name', 'patient__user__email', 'allergen', 'reaction']
    list_filter = ['severity', 'status', 'updated_at']
    ordering = ['-updated_at']