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


# Register additional models in this app module so Django discovers them.
from .no_show_predictor import NoShowPredictor, NoShowPredictor_Summary