from django.contrib import admin
from .models import MedicationInventory, DispensingTransaction, ControlledDrugLog, PharmacyAlert


@admin.register(MedicationInventory)
class MedicationInventoryAdmin(admin.ModelAdmin):
    list_display = ('medication_name', 'batch_number', 'quantity', 'unit', 'expiry_date', 'is_expired', 'is_near_expiry', 'is_controlled_drug', 'received_by')
    list_filter = ('is_expired', 'is_near_expiry', 'is_controlled_drug', 'is_blocked', 'unit', 'expiry_date')
    search_fields = ('medication_name', 'batch_number', 'manufacturer')
    readonly_fields = ('received_date', 'updated_at')
    
    fieldsets = (
        ('Medication Information', {
            'fields': ('medication_name', 'manufacturer', 'batch_number', 'lot_number')
        }),
        ('Stock Tracking', {
            'fields': ('quantity', 'unit', 'unit_cost')
        }),
        ('Dates', {
            'fields': ('manufacture_date', 'expiry_date', 'received_date', 'updated_at')
        }),
        ('Status', {
            'fields': ('is_expired', 'is_near_expiry', 'is_blocked', 'is_controlled_drug')
        }),
        ('Audit', {
            'fields': ('received_by',)
        }),
    )


@admin.register(DispensingTransaction)
class DispensingTransactionAdmin(admin.ModelAdmin):
    list_display = ('get_patient_name', 'get_medication_name', 'quantity_dispensed', 'status', 'dispensed_by', 'dispensed_at', 'is_substituted')
    list_filter = ('status', 'is_substituted', 'dispensed_at', 'dispensed_by')
    search_fields = ('patient__email', 'patient__first_name', 'patient__last_name', 'inventory__medication_name')
    readonly_fields = ('created_at', 'updated_at', 'prescription')
    
    fieldsets = (
        ('Prescription & Patient', {
            'fields': ('prescription', 'patient')
        }),
        ('Medication Details', {
            'fields': ('inventory', 'quantity_dispensed')
        }),
        ('Substitution', {
            'fields': ('is_substituted', 'substitution_reason', 'substitution_approved_by', 'substitution_approved_at')
        }),
        ('Dispensing', {
            'fields': ('status', 'dispensed_by', 'dispensed_at')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Validation', {
            'fields': ('contraindication_checked', 'contraindication_notes')
        }),
        ('Refusal/Return', {
            'fields': ('refusal_reason', 'return_reason')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}".strip()
    get_patient_name.short_description = 'Patient'
    
    def get_medication_name(self, obj):
        return obj.inventory.medication_name if obj.inventory else 'N/A'
    get_medication_name.short_description = 'Medication'


@admin.register(ControlledDrugLog)
class ControlledDrugLogAdmin(admin.ModelAdmin):
    list_display = ('medication_name', 'dea_schedule', 'log_type', 'quantity', 'unit', 'recorded_by', 'transaction_date', 'witnessed_by')
    list_filter = ('dea_schedule', 'log_type', 'transaction_date', 'recorded_by')
    search_fields = ('medication_name', 'batch_number')
    readonly_fields = ('recorded_at',)
    
    fieldsets = (
        ('Drug Information', {
            'fields': ('medication_name', 'batch_number', 'dea_schedule')
        }),
        ('Transaction', {
            'fields': ('log_type', 'quantity', 'unit', 'transaction_date')
        }),
        ('Personnel', {
            'fields': ('recorded_by', 'patient', 'witnessed_by')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('recorded_at',)
        }),
    )


@admin.register(PharmacyAlert)
class PharmacyAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'get_medication_name', 'message', 'is_resolved', 'created_at', 'resolved_by', 'resolved_at')
    list_filter = ('alert_type', 'is_resolved', 'created_at')
    search_fields = ('message', 'inventory__medication_name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Alert', {
            'fields': ('alert_type', 'inventory', 'message')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at')
        }),
        ('Audit', {
            'fields': ('created_at',)
        }),
    )
    
    def get_medication_name(self, obj):
        return obj.inventory.medication_name if obj.inventory else 'N/A'
    get_medication_name.short_description = 'Medication'
