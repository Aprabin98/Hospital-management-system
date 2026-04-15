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
    