from django.db import models
from django.utils import timezone
from datetime import timedelta


class Prescription(models.Model):
    REFILL_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('REFILLS_AVAILABLE', 'Refills Available'),
        ('NO_REFILLS', 'No Refills'),
        ('EXPIRED', 'Expired'),
        ('COMPLETED', 'Completed'),
    ]

    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='prescription'
    )
    doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    notes = models.TextField(
        blank=True,
        help_text="General notes or diagnosis"
    )
    advice = models.TextField(
        blank=True,
        help_text="Doctor's advice to patient"
    )
    follow_up_date = models.DateField(
        null=True, blank=True,
        help_text="Next follow up date"
    )
    pdf_file = models.FileField(
        upload_to='prescriptions/pdfs/',
        null=True, blank=True
    )
    
    # Refill information
    refill_status = models.CharField(
        max_length=20,
        choices=REFILL_STATUS_CHOICES,
        default='ACTIVE'
    )
    total_refills_allowed = models.IntegerField(
        default=0,
        help_text="0 = no refills allowed, -1 = unlimited"
    )
    refills_used = models.IntegerField(
        default=0,
        help_text="Number of refills already used"
    )
    refills_remaining = models.IntegerField(
        default=0,
        help_text="Remaining refills (auto-calculated)"
    )
    
    # Expiry
    expiry_date = models.DateField(
        null=True, blank=True,
        help_text="Prescription expiry date"
    )
    is_expired = models.BooleanField(default=False)
    
    # Refill notifications
    low_stock_alert_sent = models.BooleanField(default=False)
    last_refill_request_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prescription for {self.patient.full_name} by Dr.{self.doctor.user.username}"
    
    def can_refill(self):
        """Check if prescription can be refilled"""
        if self.is_expired:
            return False
        
        if self.total_refills_allowed == 0:
            return False
        
        if self.total_refills_allowed > 0 and self.refills_used >= self.total_refills_allowed:
            return False
        
        return True
    
    def request_refill(self):
        """Process a refill request"""
        if not self.can_refill():
            return False
        
        self.refills_used += 1
        self.refills_remaining = max(0, self.total_refills_allowed - self.refills_used)
        self.last_refill_request_date = timezone.now().date()
        
        # Update status
        if self.total_refills_allowed > 0 and self.refills_used >= self.total_refills_allowed:
            self.refill_status = 'NO_REFILLS'
        else:
            self.refill_status = 'REFILLS_AVAILABLE'
        
        self.save()
        return True


class PrescriptionItem(models.Model):
    FREQUENCY_CHOICES = [
        ('OD', 'Once a day'),
        ('BD', 'Twice a day'),
        ('TDS', 'Three times a day'),
        ('QDS', 'Four times a day'),
        ('SOS', 'When needed'),
        ('STAT', 'Immediately'),
    ]

    TIMING_CHOICES = [
        ('BEFORE_MEAL', 'Before Meal'),
        ('AFTER_MEAL', 'After Meal'),
        ('WITH_MEAL', 'With Meal'),
        ('EMPTY_STOMACH', 'Empty Stomach'),
        ('BEDTIME', 'Bedtime'),
        ('ANY', 'Any Time'),
    ]

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='items'
    )
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(
        max_length=100,
        help_text="e.g. 500mg, 10ml"
    )
    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='OD'
    )
    duration = models.CharField(
        max_length=100,
        help_text="e.g. 5 days, 2 weeks"
    )
    timing = models.CharField(
        max_length=20,
        choices=TIMING_CHOICES,
        default='AFTER_MEAL'
    )
    instructions = models.TextField(
        blank=True,
        help_text="Special instructions"
    )

    def __str__(self):
        return f"{self.medicine_name} - {self.dosage}"


# ===============================================
# PRESCRIPTION REFILL MANAGEMENT
# ===============================================

class PrescriptionRefill(models.Model):
    """Tracks each individual refill request"""
    STATUS_CHOICES = [
        ('REQUESTED', 'Refill Requested'),
        ('APPROVED', 'Approved by Doctor'),
        ('REJECTED', 'Rejected'),
        ('FILLED', 'Filled by Pharmacy'),
        ('EXPIRED', 'Prescription Expired'),
    ]

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='refills'
    )
    
    requested_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_refills',
        help_text="Patient or doctor requesting refill"
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='REQUESTED'
    )
    
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason for refill request"
    )
    
    requested_at = models.DateTimeField(auto_now_add=True)
    
    # Doctor approval
    approved_by = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_refills'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Pharmacy fulfillment
    filled_at = models.DateTimeField(null=True, blank=True)
    pharmacy = models.ForeignKey(
        'Pharmacy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='filled_refills'
    )
    
    # Availability
    is_urgent =models.BooleanField(
        default=False,
        help_text="Flag for urgent refills"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refill #{self.id} for Rx {self.prescription.id} - {self.get_status_display()}"
    
    class Meta:
        ordering = ['-requested_at']


class RefillReminder(models.Model):
    """Reminder to patient to request refill when prescription running low"""
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='refill_reminders'
    )
    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='refill_reminders'
    )
    
    # When to remind
    remind_when_days_remaining = models.IntegerField(
        default=7,
        help_text="Remind patient when prescription has X days supply left"
    )
    
    # Tracking
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refill reminder for {self.patient.full_name}'s Rx #{self.prescription.id}"
    
    class Meta:
        unique_together = ['prescription', 'patient']


class Pharmacy(models.Model):
    """Partner pharmacies that can fill prescriptions"""
    
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # API integration
    api_endpoint = models.URLField(blank=True)
    api_key = models.CharField(max_length=200, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


# Register additional models in this app module so Django discovers them.
from .drug_models import Drug, DrugInteraction, DrugAllergy, InteractionCheckLog