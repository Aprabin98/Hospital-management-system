from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    patient = models.ForeignKey('users.PatientProfile', on_delete=models.CASCADE, related_name='reviews')
    doctor = models.ForeignKey('clinical.Doctor', on_delete=models.CASCADE, related_name='reviews')
    appointment = models.OneToOneField('appointments.Appointment', on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['patient', 'appointment']

    def __str__(self):
        return f"Review for Dr. {self.doctor.user.username} by {self.patient.full_name} ({self.rating}/5)"
