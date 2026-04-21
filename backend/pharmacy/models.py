from django.db import models
from django.utils import timezone
from users.models import User


class MedicationInventory(models.Model):
    """
    Tracks medication stock by batch/lot/expiry.
    Each inventory record represents a specific batch of a medication.
    """
    UNIT_CHOICES = [
        ('TABLET', 'Tablet'),
        ('CAPSULE', 'Capsule'),
        ('ML', 'Milliliter'),
        ('VIAL', 'Vial'),
        ('STRIP', 'Strip'),
        ('BOTTLE', 'Bottle'),
        ('BOX', 'Box'),
    ]

    medication_name = models.CharField(max_length=255)  # e.g. "Paracetamol 500mg"
    batch_number = models.CharField(max_length=100)
    lot_number = models.CharField(max_length=100, blank=True, null=True)
    manufacturer = models.CharField(max_length=255)
    
    # Stock tracking
    quantity = models.IntegerField(help_text="Current quantity in stock")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Dates
    manufacture_date = models.DateField()
    expiry_date = models.DateField()
    received_date = models.DateField(auto_now_add=True)
    
    # Status flags
    is_near_expiry = models.BooleanField(default=False, help_text="Set when within 3 months of expiry")
    is_expired = models.BooleanField(default=False, help_text="Set when past expiry date")
    is_blocked = models.BooleanField(default=False, help_text="Blocked from dispensing if defective/recall")
    
    # Controlled drug tracking
    is_controlled_drug = models.BooleanField(default=False, help_text="CII/IV/V narcotics/psychotropics")
    
    # Audit
    received_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='medications_received')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('batch_number', 'medication_name', 'manufacturer')
        ordering = ['expiry_date', 'medication_name']
        indexes = [
            models.Index(fields=['medication_name', 'is_expired']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['is_controlled_drug']),
        ]
    
    def __str__(self):
        return f"{self.medication_name} - Batch: {self.batch_number}"
    
    def save(self, *args, **kwargs):
        # Check if expired
        today = timezone.now().date()
        self.is_expired = today > self.expiry_date
        
        # Check if near expiry (within 3 months)
        from datetime import timedelta
        three_months_from_now = today + timedelta(days=90)
        self.is_near_expiry = today <= self.expiry_date <= three_months_from_now
        
        super().save(*args, **kwargs)


class DispensingTransaction(models.Model):
    """
    Records when a pharmacist dispenses medication to fulfill a prescription.
    Links prescription to actual physical dispensing.
    """
    DISPENSING_STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('DISPENSED', 'Dispensed'),
        ('REFUSED', 'Refused'),
        ('RETURNED', 'Returned'),
    ]

    # Link to prescription
    prescription = models.ForeignKey('prescriptions.Prescription', on_delete=models.PROTECT, related_name='dispensing_transactions')
    
    # Link to patient (denormalized for quick access)
    patient = models.ForeignKey(User, on_delete=models.PROTECT, related_name='dispenses_received')
    
    # Medication details
    inventory = models.ForeignKey(MedicationInventory, on_delete=models.PROTECT, related_name='dispenses')
    quantity_dispensed = models.IntegerField()
    
    # Substitution workflow
    is_substituted = models.BooleanField(default=False, help_text="True if different from prescribed medication")
    substitution_reason = models.TextField(blank=True, null=True)
    substitution_approved_by = models.ForeignKey(
        User, on_delete=models.PROTECT, 
        related_name='substitutions_approved',
        null=True, blank=True,
        help_text="Doctor who approved substitution"
    )
    substitution_approved_at = models.DateTimeField(null=True, blank=True)
    
    # Dispensing workflow
    status = models.CharField(max_length=20, choices=DISPENSING_STATUS_CHOICES, default='PENDING')
    dispensed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transactions_dispensed')
    dispensed_at = models.DateTimeField(null=True, blank=True)
    
    # Approval workflow
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transactions_approved', null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Refusal/return
    refusal_reason = models.TextField(blank=True, null=True)
    return_reason = models.TextField(blank=True, null=True)
    
    # Contraindication checks
    contraindication_checked = models.BooleanField(default=False)
    contraindication_notes = models.TextField(blank=True, null=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['dispensed_by', '-created_at']),
        ]
    
    def __str__(self):
        return f"Dispense: {self.patient.email} - {self.inventory.medication_name}"


class ControlledDrugLog(models.Model):
    """
    Tracks controlled/CII/IV/V drugs separately for regulatory compliance.
    Every dispense of a controlled drug creates an entry in this log.
    """
    LOG_TYPE_CHOICES = [
        ('RECEIVED', 'Received from Supplier'),
        ('DISPENSED', 'Dispensed to Patient'),
        ('DESTROYED', 'Destroyed/Wasted'),
        ('RETURNED', 'Returned by Patient'),
        ('LOSS', 'Loss/Theft'),
    ]

    # What drug
    medication_name = models.CharField(max_length=255)
    batch_number = models.CharField(max_length=100)
    dea_schedule = models.CharField(
        max_length=10, 
        choices=[('II', 'Schedule II'), ('III', 'Schedule III'), ('IV', 'Schedule IV'), ('V', 'Schedule V')]
    )
    
    # Transaction details
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=20)
    
    # Who handled it
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='controlled_drug_logs_recorded')
    patient = models.ForeignKey(User, on_delete=models.PROTECT, related_name='controlled_drugs_received', null=True, blank=True, help_text="Patient if dispensed")
    
    # When
    transaction_date = models.DateField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True, help_text="Any observations (seizure, spillage, etc.)")
    
    # Audit
    witnessed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='controlled_logs_witnessed', null=True, blank=True)
    
    class Meta:
        ordering = ['-transaction_date', '-recorded_at']
        indexes = [
            models.Index(fields=['dea_schedule', '-transaction_date']),
            models.Index(fields=['recorded_by', '-transaction_date']),
        ]
    
    def __str__(self):
        return f"[{self.dea_schedule}] {self.medication_name} - {self.log_type}"


class PharmacyAlert(models.Model):
    """
    Tracks pharmacy alerts like low stock, expiry warnings, recalls.
    """
    ALERT_TYPE_CHOICES = [
        ('LOW_STOCK', 'Low Stock'),
        ('NEAR_EXPIRY', 'Near Expiry'),
        ('EXPIRED', 'Expired'),
        ('RECALL', 'Recall Notice'),
        ('CONTRAINDICATION', 'Drug Interaction'),
    ]

    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    inventory = models.ForeignKey(MedicationInventory, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='alerts_resolved', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'is_resolved']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"[{self.alert_type}] {self.message}"
