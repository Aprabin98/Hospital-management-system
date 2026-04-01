from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, help_text="Patient notes for doctor")
    pdf_file = models.FileField(upload_to='appointments/pdfs/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='appointments/qrcodes/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent double booking at database level
        unique_together = ['doctor', 'date', 'start_time']
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.patient.full_name} - Dr.{self.doctor.user.username} - {self.date} {self.start_time}"

    def can_cancel(self):
        """Patient can cancel if appointment is in future and status is PENDING or CONFIRMED."""
        from datetime import date, datetime, timedelta
        now = datetime.now()
        appointment_datetime = datetime.combine(self.date, self.start_time)
        # Can cancel if more than 2 hours before appointment
        return (
            self.status in ['PENDING', 'CONFIRMED'] and
            appointment_datetime > now + timedelta(hours=2)
        )


class WaitingList(models.Model):
    STATUS_CHOICES = [
        ('WAITING', 'Waiting'),
        ('NOTIFIED', 'Notified'),
        ('PROMOTED', 'Promoted'),
        ('CANCELLED', 'Cancelled'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='waiting_list'
    )
    doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.CASCADE,
        related_name='waiting_list'
    )
    date = models.DateField()
    priority = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='WAITING')
    notified_at = models.DateTimeField(null=True, blank=True)
    promoted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['patient', 'doctor', 'date']
        ordering = ['created_at']

    def __str__(self):
        return f"{self.patient.full_name} waiting for Dr.{self.doctor.user.username} on {self.date}"


class TriageAssessment(models.Model):
    PRIORITY_CHOICES = [
        ('P1', 'P1 - Immediate Emergency'),
        ('P2', 'P2 - Urgent Care Needed'),
        ('P3', 'P3 - Moderate Priority'),
        ('P4', 'P4 - Routine Care'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='triage_assessments'
    )
    symptoms = models.TextField(help_text='Describe current symptoms in detail.')
    duration_days = models.PositiveIntegerField(default=1)
    pain_level = models.PositiveSmallIntegerField(default=0)

    has_fever = models.BooleanField(default=False)
    has_breathing_issue = models.BooleanField(default=False)
    has_chest_pain = models.BooleanField(default=False)
    has_heavy_bleeding = models.BooleanField(default=False)
    had_fainting_episode = models.BooleanField(default=False)

    priority = models.CharField(max_length=2, choices=PRIORITY_CHOICES, default='P4')
    priority_score = models.PositiveSmallIntegerField(default=0)
    ai_summary = models.TextField(blank=True)
    recommended_action = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_triage_assessments'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_triage_assessments'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Triage {self.patient.full_name} - {self.priority} ({self.created_at.date()})"


class MedicalReportAnalysis(models.Model):
    REPORT_TYPE_CHOICES = [
        ('GENERAL', 'General Report'),
        ('CBC', 'CBC'),
        ('LIPID', 'Lipid Profile'),
        ('LIVER', 'Liver Function'),
        ('RENAL', 'Renal Function'),
        ('THYROID', 'Thyroid Panel'),
        ('DIABETES', 'Diabetes Panel'),
    ]

    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MODERATE', 'Moderate'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='report_analyses'
    )
    title = models.CharField(max_length=120, blank=True)
    report_file = models.FileField(upload_to='appointments/reports/')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='GENERAL')
    extracted_text = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    abnormal_flags = models.JSONField(default=list, blank=True)
    recommendations = models.TextField(blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='LOW')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_report_analyses'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report Analysis #{self.id} - {self.patient.full_name} ({self.risk_level})"


# Register additional models in this app module so Django discovers them.
from .no_show_predictor import NoShowPredictor, NoShowPredictor_Summary