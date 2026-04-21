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


class Queue(models.Model):
    """
    Phase 2: Queue management for receptionist board.
    Tracks both scheduled and walk-in patients in a unified queue with SLA timestamps.
    """
    STATUS_CHOICES = [
        ('WAITING', 'Waiting'),
        ('CALLED', 'Called to consultation'),
        ('IN_CONSULTATION', 'In consultation'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No show'),
        ('ARCHIVED', 'Archived'),
    ]
    
    SOURCE_CHOICES = [
        ('SCHEDULED', 'Scheduled appointment'),
        ('WALK_IN', 'Walk-in'),
        ('REFERRAL', 'Referral'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='queue_entries'
    )
    doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.CASCADE,
        related_name='queue_entries'
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='queue_entry'
    )
    
    # Queue state
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='WAITING'
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='SCHEDULED'
    )
    
    # SLA and timing
    queued_at = models.DateTimeField(auto_now_add=True)
    called_at = models.DateTimeField(null=True, blank=True)
    consultation_start = models.DateTimeField(null=True, blank=True)
    consultation_end = models.DateTimeField(null=True, blank=True)
    
    # Priority and triage
    priority = models.CharField(
        max_length=2,
        choices=[('P1', 'P1'), ('P2', 'P2'), ('P3', 'P3'), ('P4', 'P4')],
        default='P4'
    )
    triage_assessment = models.ForeignKey(
        'TriageAssessment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Notes
    notes = models.TextField(blank=True, help_text="Receptionist notes")
    
    # No-show handling
    no_show_reason = models.TextField(blank=True)
    rebooking_attempted = models.BooleanField(default=False)
    rebooking_contact_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-queued_at']
        indexes = [
            models.Index(fields=['doctor', 'status', '-queued_at']),
            models.Index(fields=['status', '-queued_at']),
        ]
    
    def __str__(self):
        return f"Queue {self.patient.full_name} - Dr.{self.doctor.user.username} - {self.status}"
    
    @property
    def wait_time_minutes(self):
        """Calculate wait time in minutes."""
        from django.utils import timezone
        if self.called_at:
            return int((self.called_at - self.queued_at).total_seconds() / 60)
        return int((timezone.now() - self.queued_at).total_seconds() / 60)
    
    @property
    def consultation_duration_minutes(self):
        """Calculate consultation duration in minutes."""
        if self.consultation_start and self.consultation_end:
            return int((self.consultation_end - self.consultation_start).total_seconds() / 60)
        return None


class PatientMatch(models.Model):
    """
    Phase 2: Fuzzy patient matching for duplicate prevention.
    Stores match scores when registering walk-ins or new referrals.
    """
    MATCH_TYPE_CHOICES = [
        ('EXACT_NAME_DOB', 'Exact name and DOB'),
        ('SIMILAR_NAME_DOB', 'Similar name and DOB'),
        ('PHONE_MATCH', 'Phone number match'),
        ('EMAIL_MATCH', 'Email match'),
    ]
    
    new_patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='match_as_new'
    )
    existing_patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='match_as_existing'
    )
    match_type = models.CharField(max_length=20, choices=MATCH_TYPE_CHOICES)
    confidence_score = models.FloatField(
        help_text="0.0 to 1.0 confidence of match"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_patient_matches'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_duplicate = models.BooleanField(null=True, blank=True, help_text="Null=pending, True=confirmed duplicate, False=not a duplicate")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['new_patient', 'existing_patient']
        ordering = ['-confidence_score']
    
    def __str__(self):
        return f"Match: {self.new_patient.full_name} vs {self.existing_patient.full_name} ({self.confidence_score:.2f})"


class NursingNote(models.Model):
    """Phase 3: Nurse handoff notes attached to appointment/patient context."""

    appointment = models.ForeignKey(
        'Appointment',
        on_delete=models.CASCADE,
        related_name='nursing_notes'
    )
    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='nursing_notes'
    )
    nurse = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nursing_notes_written'
    )
    triage_tag = models.CharField(
        max_length=2,
        choices=[('P1', 'P1'), ('P2', 'P2'), ('P3', 'P3'), ('P4', 'P4')],
        default='P4'
    )
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Nursing note for appointment #{self.appointment_id}"


class NursingTask(models.Model):
    """Phase 3: Nurse checklist tasks per appointment."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In progress'),
        ('DONE', 'Done'),
    ]

    appointment = models.ForeignKey(
        'Appointment',
        on_delete=models.CASCADE,
        related_name='nursing_tasks'
    )
    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='nursing_tasks'
    )
    title = models.CharField(max_length=120)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nursing_tasks_assigned'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nursing_tasks_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['status', '-created_at']

    def __str__(self):
        return f"Task {self.title} (#{self.appointment_id})"


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