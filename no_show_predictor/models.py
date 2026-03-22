from django.conf import settings
from django.db import models


class NoShowPredictionLog(models.Model):
    RISK_LOW = 'LOW'
    RISK_MEDIUM = 'MEDIUM'
    RISK_HIGH = 'HIGH'

    RISK_CHOICES = [
        (RISK_LOW, 'Low'),
        (RISK_MEDIUM, 'Medium'),
        (RISK_HIGH, 'High'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='no_show_predictions',
    )
    doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.CASCADE,
        related_name='no_show_predictions',
    )
    appointment_date = models.DateField()
    risk_score = models.PositiveSmallIntegerField()
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES)
    factors = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='no_show_prediction_logs',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'appointment_date']),
            models.Index(fields=['doctor', 'appointment_date']),
            models.Index(fields=['risk_level']),
        ]

    def __str__(self):
        return f'No-show risk {self.risk_score}% for patient {self.patient_id} on {self.appointment_date}'
