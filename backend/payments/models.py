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
    
    # Khalti fields
    khalti_transaction_id = models.CharField(max_length=255, null=True, blank=True)
    khalti_pidx = models.CharField(max_length=255, null=True, blank=True)
    khalti_mobile = models.CharField(max_length=20, null=True, blank=True)
    
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
    """Enhanced refund model with approval traceability"""
    STATUS_CHOICES = [
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Refund Completed'),
    ]

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='refund'
    )
    reason = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING_APPROVAL'
    )
    
    # Approval tracking
    requested_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='refunds_requested')
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='refunds_approved')
    approval_notes = models.TextField(blank=True)
    
    refunded_at = models.DateTimeField(null=True, blank=True)
    refund_method = models.CharField(max_length=50, blank=True, help_text="Method used for refund (CASH, CARD, BANK_TRANSFER)")
    refund_reference = models.CharField(max_length=100, blank=True, help_text="Transaction ID for refund")
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


# ===============================================
# PHASE 7: FINANCE & INSURANCE MATURITY
# ===============================================

class InsurancePreAuth(models.Model):
    """Insurance pre-authorization for treatments"""
    STATUS_CHOICES = [
        ('REQUESTED', 'Pre-Auth Requested'),
        ('APPROVED', 'Pre-Auth Approved'),
        ('REJECTED', 'Pre-Auth Rejected'),
        ('PARTIAL', 'Partially Approved'),
        ('EXPIRED', 'Pre-Auth Expired'),
    ]

    patient = models.ForeignKey('users.PatientProfile', on_delete=models.CASCADE)
    insurance_verification = models.ForeignKey(InsuranceVerification, on_delete=models.CASCADE)
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.CASCADE, null=True, blank=True)
    treatment_code = models.CharField(max_length=50, help_text="Medical code for procedure/treatment")
    estimated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    pre_auth_number = models.CharField(max_length=80, unique=True, null=True, blank=True)
    valid_from = models.DateField()
    valid_until = models.DateField()
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PreAuth #{self.pre_auth_number} - {self.patient.full_name} - {self.status}"


class Invoice(models.Model):
    """Invoice lifecycle: Proforma → Final Invoice"""
    TYPE_CHOICES = [
        ('PROFORMA', 'Proforma Invoice'),
        ('FINAL', 'Final Invoice'),
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued'),
        ('PAID', 'Fully Paid'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='PROFORMA')
    patient = models.ForeignKey('users.PatientProfile', on_delete=models.CASCADE, related_name='invoices')
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Line items & totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment tracking
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    due_date = models.DateField(null=True, blank=True)
    issued_date = models.DateField(null=True, blank=True)
    
    # Insurance info
    insurance_verification = models.ForeignKey(InsuranceVerification, on_delete=models.SET_NULL, null=True, blank=True)
    insurance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    patient_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Audit
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='invoices_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.invoice_number} - {self.patient.full_name} - Rs.{self.total_amount}"


class InvoiceLineItem(models.Model):
    """Line items within an invoice"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Link to original service
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    lab_booking = models.ForeignKey('lab.TestBooking', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.description} x{self.quantity} - Rs.{self.total}"


class InsuranceClaim(models.Model):
    """Insurance claim lifecycle with aging tracking"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted to Insurer'),
        ('RECEIVED', 'Received by Insurer'),
        ('PROCESSING', 'Under Processing'),
        ('APPROVED', 'Claim Approved'),
        ('REJECTED', 'Claim Rejected'),
        ('DENIED', 'Claim Denied'),
        ('APPROVED_WITH_REDUCTION', 'Approved with Reduction'),
        ('PENDING_MORE_INFO', 'Pending More Information'),
        ('REWORK_NEEDED', 'Rework Needed'),
    ]

    claim_number = models.CharField(max_length=80, unique=True)
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='claim')
    patient = models.ForeignKey('users.PatientProfile', on_delete=models.CASCADE)
    insurance_verification = models.ForeignKey(InsuranceVerification, on_delete=models.CASCADE)
    
    # Amount tracking
    claimed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reduction_reason = models.TextField(blank=True)
    
    # Status & timeline
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    submitted_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    days_pending = models.IntegerField(default=0, help_text="Days since claim submission")
    
    # Submission details
    submitted_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='claims_submitted')
    submission_reference = models.CharField(max_length=120, blank=True)
    submission_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Claim #{self.claim_number} - {self.patient.full_name} - {self.status}"


class ClaimAuditLog(models.Model):
    """Audit trail for all claim status changes"""
    claim = models.ForeignKey(InsuranceClaim, on_delete=models.CASCADE, related_name='audit_logs')
    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    change_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.claim.claim_number}: {self.old_status} → {self.new_status}"


class DenialRework(models.Model):
    """Queue for denied claims requiring rework"""
    STATUS_CHOICES = [
        ('PENDING_REVIEW', 'Pending Review'),
        ('UNDER_CORRECTION', 'Under Correction'),
        ('RESUBMITTED', 'Resubmitted'),
        ('RESOLVED', 'Resolved'),
        ('ABANDONED', 'Abandoned'),
    ]

    claim = models.OneToOneField(InsuranceClaim, on_delete=models.CASCADE, related_name='denial_rework')
    original_denial_reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_REVIEW')
    assigned_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='denial_reworks')
    correction_notes = models.TextField(blank=True)
    resubmit_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rework for Claim #{self.claim.claim_number} - {self.status}"