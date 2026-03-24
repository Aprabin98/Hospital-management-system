from django.db import models
from django.utils import timezone
from datetime import timedelta


class Payment(models.Model):
    STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
        ('OVERDUE', 'Overdue'),
        ('PARTIALLY_PAID', 'Partially Paid'),
    ]

    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('KHALTI', 'Khalti'),
        ('ESEWA', 'eSewa'),
        ('ONLINE', 'Online'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('APPOINTMENT', 'Appointment'),
        ('LAB_TEST', 'Lab Test'),
        ('ADMISSION', 'Hospital Admission'),
        ('CONSULTATION', 'Consultation'),
        ('OTHER', 'Other'),
    ]

    payment_type = models.CharField(
        max_length=15,
        choices=PAYMENT_TYPE_CHOICES,
        default='APPOINTMENT'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='payments',
        null=True, blank=True
    )
    lab_booking = models.ForeignKey(
        'lab.TestBooking',
        on_delete=models.CASCADE,
        related_name='payments',
        null=True, blank=True
    )

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.CASCADE,
        related_name='payments',
        null=True, blank=True
    )
    
    # Store amount at time of booking (fee might change later)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0,
        help_text="Track partial payments"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='UNPAID'
    )
    payment_method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES,
        default='CASH',
        blank=True
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(
        null=True, blank=True,
        help_text="Expected payment deadline"
    )
    receipt_file = models.FileField(
        upload_to='payments/receipts/',
        null=True, blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Reminder tracking
    reminder_sent_count = models.IntegerField(default=0)
    last_reminder_sent = models.DateTimeField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)
    overdue_days = models.IntegerField(default=0)

    def __str__(self):
        return f"Payment #{self.id} - {self.patient.full_name} - Rs.{self.amount} - {self.status}"
    
    def calculate_overdue_status(self):
        """Calculate if payment is overdue and update status"""
        if self.status in ['PAID', 'REFUNDED']:
            return False
        
        if self.due_date and self.due_date < timezone.now().date():
            self.is_overdue = True
            self.overdue_days = (timezone.now().date() - self.due_date).days
            
            if self.status == 'UNPAID':
                self.status = 'OVERDUE'
            
            self.save(update_fields=['is_overdue', 'overdue_days', 'status'])
            return True
        
        return False


class Refund(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='refund'
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    refunded_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund for Payment #{self.payment.id} - {self.status}"


# ===============================================
# PAYMENT REMINDER SYSTEM
# ===============================================

class PaymentReminder(models.Model):
    """Tracks payment reminder settings and history"""
    REMINDER_TYPE_CHOICES = [
        ('AUTO', 'Automatic Reminders'),
        ('MANUAL', 'Manual Reminders'),
    ]

    CHANNEL_CHOICES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('WHATSAPP', 'WhatsApp'),
        ('IN_APP', 'In-App Notification'),
        ('ALL', 'All Channels'),
    ]

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='reminder'
    )
    
    # Reminder configuration
    reminder_type = models.CharField(
        max_length=10,
        choices=REMINDER_TYPE_CHOICES,
        default='AUTO'
    )
    channel = models.CharField(
        max_length=10,
        choices=CHANNEL_CHOICES,
        default='ALL'
    )
    
    # Schedule
    first_reminder_days_before = models.IntegerField(
        default=3,
        help_text="Send reminder X days before due date"
    )
    second_reminder_days_after = models.IntegerField(
        default=2,
        help_text="Send reminder X days after due date if unpaid"
    )
    final_reminder_days_after = models.IntegerField(
        default=7,
        help_text="Final reminder X days after due date"
    )
    
    # Tracking
    first_reminder_sent = models.BooleanField(default=False)
    first_reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    second_reminder_sent = models.BooleanField(default=False)
    second_reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    final_reminder_sent = models.BooleanField(default=False)
    final_reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    disabled_reason = models.TextField(blank=True)
    disabled_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disabled_reminders'
    )
    disabled_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reminder for Payment #{self.payment.id}"
    
    def should_send_first_reminder(self):
        """Check if first reminder should be sent"""
        if not self.payment.due_date or self.first_reminder_sent:
            return False
        
        days_until_due = (self.payment.due_date - timezone.now().date()).days
        return days_until_due == self.first_reminder_days_before
    
    def should_send_second_reminder(self):
        """Check if second reminder should be sent"""
        if not self.payment.due_date or self.second_reminder_sent:
            return False
        
        days_past_due = (timezone.now().date() - self.payment.due_date).days
        return days_past_due == self.second_reminder_days_after and self.payment.status in ['UNPAID', 'OVERDUE']
    
    def should_send_final_reminder(self):
        """Check if final reminder should be sent"""
        if not self.payment.due_date or self.final_reminder_sent:
            return False
        
        days_past_due = (timezone.now().date() - self.payment.due_date).days
        return days_past_due == self.final_reminder_days_after and self.payment.status in ['UNPAID', 'OVERDUE']


class PaymentReminderLog(models.Model):
    """Logs all payment reminders sent"""
    STATUS_CHOICES = [
        ('SENT', 'Sent Successfully'),
        ('FAILED', 'Failed to Send'),
        ('BOUNCED', 'Bounced'),
        ('OPTIMAL', 'Optimal Delivery'),
    ]

    reminder = models.ForeignKey(
        PaymentReminder,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='reminder_logs'
    )
    
    reminder_number = models.IntegerField(
        choices=[(1, '1st'), (2, '2nd'), (3, 'Final')],
        help_text="Which reminder in sequence"
    )
    channel = models.CharField(max_length=10)
    recipient = models.CharField(
        max_length=255,
        help_text="Email address, phone, etc."
    )
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SENT')
    error_message = models.TextField(blank=True)
    
    message_preview = models.TextField(blank=True)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    read_status = models.BooleanField(default=False)

    def __str__(self):
        return f"Reminder #{self.reminder_number} for Payment #{self.payment.id} - {self.status}"
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name_plural = 'Payment Reminder Logs'


class InsuranceVerification(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='insurance_verifications'
    )
    provider_name = models.CharField(max_length=150)
    policy_number = models.CharField(max_length=80)
    plan_name = models.CharField(max_length=120, blank=True)
    coverage_percent = models.PositiveSmallIntegerField(default=0)
    valid_until = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    verified_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insurance_verifications_done'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    external_reference = models.CharField(max_length=120, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['patient', 'provider_name', 'policy_number']

    def __str__(self):
        return f"{self.patient.full_name} - {self.provider_name} ({self.status})"

    def mark_expired_if_needed(self):
        if self.valid_until and self.valid_until < timezone.now().date() and self.status == 'VERIFIED':
            self.status = 'EXPIRED'
            self.save(update_fields=['status', 'updated_at'])