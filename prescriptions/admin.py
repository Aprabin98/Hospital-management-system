from django.contrib import admin
from .models import Prescription, PrescriptionItem, PrescriptionRefill, RefillReminder, Pharmacy
from .drug_models import Drug, DrugInteraction, DrugAllergy, InteractionCheckLog


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'appointment', 'created_at']
    search_fields = ['patient__full_name', 'doctor__user__username']
    inlines = [PrescriptionItemInline]
    ordering = ['-created_at']


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ['medicine_name', 'dosage', 'frequency', 'duration', 'timing']


@admin.register(PrescriptionRefill)
class PrescriptionRefillAdmin(admin.ModelAdmin):
    list_display = ['id', 'prescription', 'status', 'requested_by', 'requested_at', 'pharmacy']
    list_filter = ['status', 'is_urgent']
    search_fields = ['prescription__patient__full_name', 'prescription__doctor__user__username']
    ordering = ['-requested_at']


@admin.register(RefillReminder)
class RefillReminderAdmin(admin.ModelAdmin):
    list_display = ['prescription', 'patient', 'remind_when_days_remaining', 'reminder_sent', 'is_active']
    list_filter = ['reminder_sent', 'is_active']


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'phone', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'location', 'phone']


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = ['generic_name', 'category', 'strength', 'is_active']
    list_filter = ['category', 'is_active', 'pregnancy_category']
    search_fields = ['generic_name', 'brand_names']


@admin.register(DrugInteraction)
class DrugInteractionAdmin(admin.ModelAdmin):
    list_display = ['drug1', 'drug2', 'severity', 'interaction_type', 'is_active']
    list_filter = ['severity', 'interaction_type', 'is_active']
    search_fields = ['drug1__generic_name', 'drug2__generic_name']


@admin.register(DrugAllergy)
class DrugAllergyAdmin(admin.ModelAdmin):
    list_display = ['patient', 'drug', 'severity', 'is_confirmed', 'created_at']
    list_filter = ['severity', 'is_confirmed']
    search_fields = ['patient__full_name', 'drug__generic_name']


@admin.register(InteractionCheckLog)
class InteractionCheckLogAdmin(admin.ModelAdmin):
    list_display = ['prescription', 'checked_by', 'interactions_found', 'major_interactions', 'allergies_found', 'checked_at']
    list_filter = ['cleared_by_doctor']
    search_fields = ['prescription__patient__full_name', 'checked_by__username']
    ordering = ['-checked_at']