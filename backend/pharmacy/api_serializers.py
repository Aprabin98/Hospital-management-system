from rest_framework import serializers
from .models import MedicationInventory, DispensingTransaction, ControlledDrugLog, PharmacyAlert


class MedicationInventorySerializer(serializers.ModelSerializer):
    received_by_name = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    days_to_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicationInventory
        fields = [
            'id', 'medication_name', 'batch_number', 'lot_number', 'manufacturer',
            'quantity', 'unit', 'unit_cost', 'total_value',
            'manufacture_date', 'expiry_date', 'days_to_expiry', 'received_date',
            'is_near_expiry', 'is_expired', 'is_blocked', 'is_controlled_drug',
            'received_by', 'received_by_name', 'updated_at'
        ]
    
    def get_received_by_name(self, obj):
        if obj.received_by:
            return f"{obj.received_by.first_name} {obj.received_by.last_name}".strip()
        return 'System'
    
    def get_total_value(self, obj):
        return float(obj.quantity * obj.unit_cost)
    
    def get_days_to_expiry(self, obj):
        from datetime import datetime, date
        if isinstance(obj.expiry_date, datetime):
            expiry = obj.expiry_date.date()
        else:
            expiry = obj.expiry_date
        
        today = date.today()
        delta = expiry - today
        return delta.days


class DispensingTransactionSerializer(serializers.ModelSerializer):
    dispensed_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    substitution_approved_by_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    prescription_details = serializers.SerializerMethodField()
    medication_details = serializers.SerializerMethodField()
    
    class Meta:
        model = DispensingTransaction
        fields = [
            'id', 'prescription', 'prescription_details', 'patient', 'patient_name',
            'inventory', 'medication_details', 'quantity_dispensed',
            'is_substituted', 'substitution_reason', 'substitution_approved_by', 'substitution_approved_by_name',
            'substitution_approved_at',
            'status', 'dispensed_by', 'dispensed_by_name', 'dispensed_at',
            'approved_by', 'approved_by_name', 'approved_at',
            'refusal_reason', 'return_reason',
            'contraindication_checked', 'contraindication_notes',
            'created_at', 'updated_at'
        ]
    
    def get_dispensed_by_name(self, obj):
        if obj.dispensed_by:
            return f"{obj.dispensed_by.first_name} {obj.dispensed_by.last_name}".strip()
        return 'System'
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.first_name} {obj.approved_by.last_name}".strip()
        return None
    
    def get_substitution_approved_by_name(self, obj):
        if obj.substitution_approved_by:
            return f"{obj.substitution_approved_by.first_name} {obj.substitution_approved_by.last_name}".strip()
        return None
    
    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}".strip()
        return obj.patient.email if obj.patient else 'Unknown'
    
    def get_prescription_details(self, obj):
        if obj.prescription:
            return {
                'id': obj.prescription.id,
                'medicine_name': obj.prescription.medicine_name,
                'dosage': obj.prescription.dosage,
                'frequency': obj.prescription.frequency,
                'duration': obj.prescription.duration,
            }
        return None
    
    def get_medication_details(self, obj):
        if obj.inventory:
            return {
                'id': obj.inventory.id,
                'medication_name': obj.inventory.medication_name,
                'batch_number': obj.inventory.batch_number,
                'expiry_date': obj.inventory.expiry_date,
                'quantity_available': obj.inventory.quantity,
            }
        return None


class ControlledDrugLogSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.SerializerMethodField()
    witnessed_by_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ControlledDrugLog
        fields = [
            'id', 'medication_name', 'batch_number', 'dea_schedule',
            'log_type', 'quantity', 'unit',
            'recorded_by', 'recorded_by_name',
            'patient', 'patient_name',
            'transaction_date', 'recorded_at',
            'notes',
            'witnessed_by', 'witnessed_by_name'
        ]
    
    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return f"{obj.recorded_by.first_name} {obj.recorded_by.last_name}".strip()
        return 'System'
    
    def get_witnessed_by_name(self, obj):
        if obj.witnessed_by:
            return f"{obj.witnessed_by.first_name} {obj.witnessed_by.last_name}".strip()
        return None
    
    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}".strip()
        return None


class PharmacyAlertSerializer(serializers.ModelSerializer):
    resolved_by_name = serializers.SerializerMethodField()
    inventory_details = serializers.SerializerMethodField()
    
    class Meta:
        model = PharmacyAlert
        fields = [
            'id', 'alert_type', 'inventory', 'inventory_details',
            'message', 'is_resolved', 'resolved_at',
            'resolved_by', 'resolved_by_name', 'created_at'
        ]
    
    def get_resolved_by_name(self, obj):
        if obj.resolved_by:
            return f"{obj.resolved_by.first_name} {obj.resolved_by.last_name}".strip()
        return None
    
    def get_inventory_details(self, obj):
        if obj.inventory:
            return {
                'id': obj.inventory.id,
                'medication_name': obj.inventory.medication_name,
                'batch_number': obj.inventory.batch_number,
                'quantity': obj.inventory.quantity,
            }
        return None
