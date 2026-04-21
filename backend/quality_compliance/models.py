from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class IncidentReport(models.Model):
    INCIDENT_TYPE_CHOICES = [
        ('QUALITY', 'Quality'),
        ('SAFETY', 'Safety'),
        ('SECURITY', 'Security'),
        ('OPERATIONAL', 'Operational'),
        ('CLINICAL', 'Clinical'),
    ]

    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('TRIAGED', 'Triaged'),
        ('INVESTIGATING', 'Investigating'),
        ('RCA_COMPLETE', 'Root Cause Complete'),
        ('CLOSED', 'Closed'),
    ]

    title = models.CharField(max_length=255)
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPE_CHOICES, default='QUALITY')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    description = models.TextField()
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    closure_notes = models.TextField(blank=True)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incident_reports_created',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incident_reports_assigned',
    )
    reported_at = models.DateTimeField(auto_now_add=True)
    triaged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-reported_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['incident_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['reported_at']),
        ]

    def __str__(self):
        return f'{self.title} ({self.status})'


class SlaBreach(models.Model):
    BREACH_CATEGORY_CHOICES = [
        ('APPOINTMENT', 'Appointment'),
        ('LAB', 'Lab'),
        ('PHARMACY', 'Pharmacy'),
        ('BILLING', 'Billing'),
        ('IPD', 'Inpatient'),
        ('GENERAL', 'General'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('ESCALATED', 'Escalated'),
        ('RESOLVED', 'Resolved'),
        ('WAIVED', 'Waived'),
    ]

    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    process_name = models.CharField(max_length=255)
    reference_number = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=20, choices=BREACH_CATEGORY_CHOICES, default='GENERAL')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    expected_at = models.DateTimeField()
    breached_at = models.DateTimeField(auto_now_add=True)
    owner_role = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    resolution_summary = models.TextField(blank=True)
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sla_breaches_escalated_to',
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sla_breaches_acknowledged',
    )
    escalated_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-breached_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['severity']),
            models.Index(fields=['expected_at']),
        ]

    def __str__(self):
        return f'{self.process_name} ({self.status})'


class BackupRestoreDrill(models.Model):
    DRILL_TYPE_CHOICES = [
        ('BACKUP', 'Backup'),
        ('RESTORE', 'Restore'),
        ('FULL', 'Full Drill'),
    ]

    drill_type = models.CharField(max_length=20, choices=DRILL_TYPE_CHOICES, default='BACKUP')
    environment = models.CharField(max_length=100, default='Production')
    runbook_version = models.CharField(max_length=50, blank=True)
    success = models.BooleanField(default=False)
    duration_minutes = models.PositiveIntegerField(default=0)
    rpo_minutes = models.PositiveIntegerField(null=True, blank=True)
    rto_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    evidence_url = models.URLField(blank=True)
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backup_drills_executed',
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backup_drills_verified',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['drill_type']),
            models.Index(fields=['success']),
            models.Index(fields=['executed_at']),
        ]

    def __str__(self):
        return f'{self.drill_type} drill on {self.environment}'

    @property
    def next_due_at(self):
        return self.executed_at + timedelta(days=30)


class RetentionPolicy(models.Model):
    module_name = models.CharField(max_length=120)
    policy_name = models.CharField(max_length=255)
    retention_days = models.PositiveIntegerField(default=365)
    archive_after_days = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    owner_role = models.CharField(max_length=30, blank=True)
    summary = models.TextField(blank=True)
    last_executed_at = models.DateTimeField(null=True, blank=True)
    next_review_at = models.DateField(null=True, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retention_policies_updated',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['module_name', 'policy_name']
        indexes = [
            models.Index(fields=['active']),
            models.Index(fields=['module_name']),
            models.Index(fields=['next_review_at']),
        ]

    def __str__(self):
        return f'{self.module_name}: {self.policy_name}'