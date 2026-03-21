from django.db import models


class Prescription(models.Model):
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='prescription'
    )
    doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    notes = models.TextField(
        blank=True,
        help_text="General notes or diagnosis"
    )
    advice = models.TextField(
        blank=True,
        help_text="Doctor's advice to patient"
    )
    follow_up_date = models.DateField(
        null=True, blank=True,
        help_text="Next follow up date"
    )
    pdf_file = models.FileField(
        upload_to='prescriptions/pdfs/',
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prescription for {self.patient.full_name} by Dr.{self.doctor.user.username}"


class PrescriptionItem(models.Model):
    FREQUENCY_CHOICES = [
        ('OD', 'Once a day'),
        ('BD', 'Twice a day'),
        ('TDS', 'Three times a day'),
        ('QDS', 'Four times a day'),
        ('SOS', 'When needed'),
        ('STAT', 'Immediately'),
    ]

    TIMING_CHOICES = [
        ('BEFORE_MEAL', 'Before Meal'),
        ('AFTER_MEAL', 'After Meal'),
        ('WITH_MEAL', 'With Meal'),
        ('EMPTY_STOMACH', 'Empty Stomach'),
        ('BEDTIME', 'Bedtime'),
        ('ANY', 'Any Time'),
    ]

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='items'
    )
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(
        max_length=100,
        help_text="e.g. 500mg, 10ml"
    )
    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='OD'
    )
    duration = models.CharField(
        max_length=100,
        help_text="e.g. 5 days, 2 weeks"
    )
    timing = models.CharField(
        max_length=20,
        choices=TIMING_CHOICES,
        default='AFTER_MEAL'
    )
    instructions = models.TextField(
        blank=True,
        help_text="Special instructions"
    )

    def __str__(self):
        return f"{self.medicine_name} - {self.dosage}"