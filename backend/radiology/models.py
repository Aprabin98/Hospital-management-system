from django.db import models


class ImagingCatalog(models.Model):
    MODALITY_CHOICES = [
        ('XRAY', 'X-Ray'),
        ('CT', 'CT Scan'),
        ('MRI', 'MRI'),
        ('USG', 'Ultrasound'),
        ('MAMMO', 'Mammography'),
        ('ECHO', 'Echocardiography'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=180, unique=True)
    modality = models.CharField(max_length=20, choices=MODALITY_CHOICES, default='XRAY')
    description = models.TextField(blank=True)
    preparation = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    turnaround_hours = models.PositiveIntegerField(default=24)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.modality})"


class ImagingOrder(models.Model):
    PRIORITY_CHOICES = [
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent'),
        ('STAT', 'Stat'),
    ]

    STATUS_CHOICES = [
        ('ORDERED', 'Ordered'),
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('REPORTED', 'Reported'),
        ('RELEASED', 'Released'),
        ('CANCELLED', 'Cancelled'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='imaging_orders',
    )
    catalog_item = models.ForeignKey(
        ImagingCatalog,
        on_delete=models.PROTECT,
        related_name='orders',
    )
    ordered_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordered_imaging',
    )
    assigned_radiologist = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='radiology_assignments',
    )
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='ROUTINE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ORDERED')
    clinical_notes = models.TextField(blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
        ]

    def __str__(self):
        return f"IMG-{self.id} {self.patient.full_name}"


class ImagingReport(models.Model):
    REPORT_STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('FINAL', 'Final'),
    ]

    order = models.OneToOneField(
        ImagingOrder,
        on_delete=models.CASCADE,
        related_name='report',
    )
    findings = models.TextField(blank=True)
    impression = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    report_status = models.CharField(max_length=15, choices=REPORT_STATUS_CHOICES, default='DRAFT')
    is_critical = models.BooleanField(default=False)
    critical_notified_at = models.DateTimeField(null=True, blank=True)
    reported_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='radiology_reports',
    )
    released_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='released_radiology_reports',
    )
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Report for IMG-{self.order_id}"


class ImagingAttachment(models.Model):
    order = models.ForeignKey(
        ImagingOrder,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file_url = models.URLField(max_length=500)
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    metadata_json = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='radiology_attachments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Attachment for IMG-{self.order_id}: {self.file_name}"
