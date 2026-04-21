from django.db import models
from django.utils import timezone


class TestTemplate(models.Model):
    """Admin creates test templates like Blood Sugar, CBC etc."""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    preparation = models.TextField(
        blank=True,
        help_text="Instructions before test e.g. Fast for 8 hours"
    )
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.IntegerField(
        default=30,
        help_text="How long the test takes"
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class TestField(models.Model):
    """Fields inside a test template e.g. Fasting Blood Sugar."""
    FIELD_TYPE_CHOICES = [
        ('NUMBER', 'Number'),
        ('TEXT', 'Text'),
    ]

    template = models.ForeignKey(
        TestTemplate,
        on_delete=models.CASCADE,
        related_name='fields'
    )
    field_name = models.CharField(
        max_length=200,
        help_text="e.g. Fasting Blood Sugar"
    )
    unit = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. mg/dL, g/dL"
    )
    normal_min = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Normal range minimum"
    )
    normal_max = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Normal range maximum"
    )
    critical_min = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Critical low value threshold"
    )
    critical_max = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Critical high value threshold"
    )
    normal_text = models.CharField(
        max_length=100,
        blank=True,
        help_text="For text fields e.g. Negative"
    )
    field_type = models.CharField(
        max_length=10,
        choices=FIELD_TYPE_CHOICES,
        default='NUMBER'
    )
    is_required = models.BooleanField(
        default=False,
        help_text="If False, lab can leave it blank (shows — in report)"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order in report"
    )

    def __str__(self):
        return f"{self.template.name} - {self.field_name}"

    class Meta:
        ordering = ['order', 'id']


class TestSchedule(models.Model):
    """When can this test be done."""
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]

    template = models.ForeignKey(
        TestTemplate,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_bookings = models.IntegerField(
        default=20,
        help_text="Max patients per day for this test"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.template.name} - {self.day}"

    class Meta:
        unique_together = ['template', 'day']
        ordering = ['day']


class TestBooking(models.Model):
    """Patient books a lab test."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SAMPLE_COLLECTED', 'Sample Collected'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('REJECTED_SAMPLE', 'Rejected Sample'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='test_bookings'
    )
    template = models.ForeignKey(
        TestTemplate,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='UNPAID'
    )
    amount = models.DecimalField(
        max_digits=8, decimal_places=2,
        help_text="Price at time of booking"
    )
    notes = models.TextField(blank=True)
    specimen_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
    collected_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collected_samples'
    )
    collected_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.CharField(max_length=255, blank=True)
    expected_report_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.template.name} - {self.date}"

    class Meta:
        # No same test on same date for same patient
        unique_together = ['patient', 'template', 'date']
        ordering = ['-date']


class TestRecommendation(models.Model):
    """Doctor/staff recommendation for a patient to book a lab test."""
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('BOOKED', 'Booked'),
        ('COMPLETED', 'Completed'),
        ('DECLINED', 'Declined'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='test_recommendations'
    )
    template = models.ForeignKey(
        TestTemplate,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    recommended_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommended_tests'
    )
    doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_recommendations'
    )
    reason = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.template.name} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['patient', 'template', 'status']


class TestResult(models.Model):
    """Lab technician fills test results with workflow status tracking."""
    STATUS_CHOICES = [
        ('PENDING', 'Awaiting Lab Entry'),
        ('ENTERED', 'Results Entered'),
        ('REVIEWED', 'Under Doctor Review'),
        ('APPROVED', 'Approved by Doctor'),
        ('RELEASED', 'Released to Patient'),
        ('CANCELLED', 'Cancelled'),
    ]

    booking = models.OneToOneField(
        TestBooking,
        on_delete=models.CASCADE,
        related_name='result'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="Workflow status of result"
    )
    filled_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='filled_results'
    )
    notes = models.TextField(
        blank=True,
        help_text="Lab technician notes"
    )
    pdf_file = models.FileField(
        upload_to='lab/reports/',
        null=True, blank=True
    )
    is_released = models.BooleanField(
        default=False,
        help_text="Admin releases report to patient"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Authorized reviewer verified the report before release"
    )
    verified_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_results'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_results',
        help_text="Doctor who reviewed and approved results"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    filled_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    has_critical_values = models.BooleanField(
        default=False,
        help_text="Auto-flagged if any result item is critical"
    )
    critical_notification_sent = models.BooleanField(
        default=False,
        help_text="Track if critical values notification was sent to doctor"
    )

    def __str__(self):
        return f"Result for {self.booking} - {self.get_status_display()}"
    
    def check_critical_values(self):
        """Check if any result items are critical"""
        return self.items.filter(is_critical=True).exists()


class TestResultItem(models.Model):
    """Individual field value in a test result."""
    STATUS_CHOICES = [
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('LOW', 'Low'),
        ('ABNORMAL', 'Abnormal'),
        ('NOT_DONE', 'Not Done'),
    ]

    result = models.ForeignKey(
        TestResult,
        on_delete=models.CASCADE,
        related_name='items'
    )
    field = models.ForeignKey(
        TestField,
        on_delete=models.CASCADE
    )
    value = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Leave blank if test not done for this field"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='NOT_DONE'
    )
    is_critical = models.BooleanField(default=False)

    def calculate_status(self):
        """Auto calculate Normal/High/Low based on value and normal range."""
        if not self.value or self.value.strip() == '':
            return 'NOT_DONE'

        if self.field.field_type == 'NUMBER':
            try:
                val = float(self.value)
                if self.field.normal_min and self.field.normal_max:
                    if val < float(self.field.normal_min):
                        return 'LOW'
                    elif val > float(self.field.normal_max):
                        return 'HIGH'
                    else:
                        return 'NORMAL'
            except ValueError:
                return 'ABNORMAL'
        else:
            # Text field
            if self.field.normal_text:
                if self.value.strip().lower() == self.field.normal_text.strip().lower():
                    return 'NORMAL'
                else:
                    return 'ABNORMAL'

        return 'NORMAL'

    def calculate_critical(self):
        if not self.value or self.value.strip() == '' or self.field.field_type != 'NUMBER':
            return False

        try:
            val = float(self.value)
        except ValueError:
            return False

        if self.field.critical_min is not None and val < float(self.field.critical_min):
            return True
        if self.field.critical_max is not None and val > float(self.field.critical_max):
            return True
        return False

    def save(self, *args, **kwargs):
        self.status = self.calculate_status()
        self.is_critical = self.calculate_critical()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.field.field_name}: {self.value or '—'}"


# ==================== PHASE 4: Lab Lifecycle Models ====================

class LabSample(models.Model):
    """Phase 4: Sample accession with barcode tracking and status lifecycle."""
    STATUS_CHOICES = [
        ('COLLECTED', 'Sample Collected'),
        ('IN_PROCESS', 'In Process'),
        ('VALIDATED', 'Validated'),
        ('RELEASED', 'Released'),
        ('REJECTED', 'Rejected'),
        ('RECOLLECT', 'Recollect Requested'),
    ]

    result = models.OneToOneField(
        TestResult,
        on_delete=models.CASCADE,
        related_name='sample'
    )
    barcode_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique barcode for sample tracking"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='COLLECTED'
    )
    collected_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_samples_collected',
        help_text="Staff who collected the sample"
    )
    collected_at = models.DateTimeField(null=True, blank=True)
    
    processed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_samples_processed',
        help_text="Lab tech who processed the sample"
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    validated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_samples_validated',
        help_text="Lab supervisor who validated the sample"
    )
    validated_at = models.DateTimeField(null=True, blank=True)
    
    rejection_reason = models.TextField(blank=True, help_text="Why sample was rejected")
    recollect_reason = models.TextField(blank=True, help_text="Why recollection is needed")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Sample {self.barcode_id} - {self.get_status_display()}"

    class Meta:
        ordering = ['-created_at']


class QCLog(models.Model):
    """Phase 4: Quality control and calibration logs."""
    QC_TYPE_CHOICES = [
        ('CALIBRATION', 'Equipment Calibration'),
        ('QUALITY_CONTROL', 'Quality Control Check'),
        ('MAINTENANCE', 'Equipment Maintenance'),
        ('VALIDATION', 'Test Validation'),
    ]

    sample = models.ForeignKey(
        LabSample,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='qc_logs',
        help_text="Optional: Link to specific sample if QC relates to one"
    )
    qc_type = models.CharField(
        max_length=20,
        choices=QC_TYPE_CHOICES,
        default='QUALITY_CONTROL'
    )
    test_template = models.ForeignKey(
        TestTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qc_logs'
    )
    performed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='qc_logs_performed'
    )
    result = models.CharField(
        max_length=50,
        choices=[
            ('PASSED', 'Passed'),
            ('FAILED', 'Failed'),
            ('CONDITIONAL', 'Conditional Pass'),
        ],
        default='PASSED'
    )
    details = models.TextField(help_text="QC details, calibration values, or findings")
    reference_value = models.CharField(max_length=100, blank=True)
    actual_value = models.CharField(max_length=100, blank=True)
    deviation = models.CharField(max_length=100, blank=True, help_text="Acceptable deviation percentage or range")
    
    performed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.get_qc_type_display()} - {self.get_result_display()}"


class CriticalValueAcknowledgment(models.Model):
    """Phase 4: Doctor acknowledgment of critical lab values."""
    URGENCY_CHOICES = [
        ('IMMEDIATE', 'Immediate (Life-threatening)'),
        ('URGENT', 'Urgent (Within 1 hour)'),
        ('PRIORITY', 'Priority (Within 4 hours)'),
    ]

    result = models.OneToOneField(
        TestResult,
        on_delete=models.CASCADE,
        related_name='critical_acknowledgment'
    )
    
    # Critical value details
    is_critical = models.BooleanField(default=True, help_text="Flag if this is truly critical")
    urgency = models.CharField(
        max_length=15,
        choices=URGENCY_CHOICES,
        default='URGENT'
    )
    critical_fields = models.JSONField(default=list, help_text="List of critical field IDs and their values")
    
    # Notification tracking
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    notification_method = models.CharField(
        max_length=50,
        choices=[
            ('SMS', 'SMS'),
            ('EMAIL', 'Email'),
            ('PUSH', 'Push Notification'),
            ('PHONE', 'Phone Call'),
            ('MANUAL', 'Manual Contact'),
        ],
        default='SMS',
        help_text="How the doctor was notified"
    )
    
    # Doctor acknowledgment
    acknowledged_by = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='critical_value_acknowledgments',
        help_text="Doctor who acknowledged the critical value"
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledgment_notes = models.TextField(blank=True, help_text="Doctor's response or action taken")
    
    # Escalation tracking
    escalated_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_critical_values',
        help_text="If not acknowledged, escalated to senior/admin"
    )
    escalated_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Acknowledged" if self.acknowledged_at else "Pending"
        return f"Critical Value - {status} ({self.urgency})"

    class Meta:
        ordering = ['-created_at']
    