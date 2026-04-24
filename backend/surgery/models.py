from django.db import models
from django.utils import timezone


class OTSchedule(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    patient = models.ForeignKey('users.PatientProfile', on_delete=models.CASCADE, related_name='ot_schedules')
    inpatient_stay = models.ForeignKey('inpatient.InpatientStay', on_delete=models.SET_NULL, null=True, blank=True, related_name='ot_schedules')
    surgeon = models.ForeignKey('clinical.Doctor', on_delete=models.SET_NULL, null=True, blank=True, related_name='surgeries_as_surgeon')
    anesthetist = models.ForeignKey('clinical.Doctor', on_delete=models.SET_NULL, null=True, blank=True, related_name='surgeries_as_anesthetist')
    procedure_name = models.CharField(max_length=255)
    ot_room = models.CharField(max_length=80)
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    pre_op_checklist = models.TextField(blank=True)
    surgery_billing_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='created_ot_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_start']
        indexes = [
            models.Index(fields=['status', 'scheduled_start']),
            models.Index(fields=['ot_room', 'scheduled_start']),
        ]

    def __str__(self):
        return f"OT-{self.id} {self.procedure_name}"


class ProcedureNote(models.Model):
    schedule = models.OneToOneField(OTSchedule, on_delete=models.CASCADE, related_name='procedure_note')
    procedure_steps = models.TextField()
    findings = models.TextField(blank=True)
    complications = models.TextField(blank=True)
    anesthesia_notes = models.TextField(blank=True)
    signed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='signed_procedure_notes')
    signed_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']


class PostOpNote(models.Model):
    RECOVERY_CHOICES = [
        ('STABLE', 'Stable'),
        ('OBSERVATION', 'Observation'),
        ('CRITICAL', 'Critical'),
    ]

    schedule = models.ForeignKey(OTSchedule, on_delete=models.CASCADE, related_name='post_op_notes')
    recovery_status = models.CharField(max_length=20, choices=RECOVERY_CHOICES, default='OBSERVATION')
    pain_score = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField()
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='post_op_notes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
