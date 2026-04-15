from django.conf import settings
from django.db import models


class HeartRiskAssessment(models.Model):
    RISK_LOW = 'LOW'
    RISK_MEDIUM = 'MEDIUM'
    RISK_HIGH = 'HIGH'

    RISK_LEVEL_CHOICES = [
        (RISK_LOW, 'Low'),
        (RISK_MEDIUM, 'Medium'),
        (RISK_HIGH, 'High'),
    ]

    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='heart_risk_assessments',
    )
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='heart_risk_assessments',
    )
    doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='heart_risk_assessments',
    )

    age = models.PositiveSmallIntegerField()
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    systolic_bp = models.PositiveSmallIntegerField()
    diastolic_bp = models.PositiveSmallIntegerField()
    total_cholesterol = models.PositiveSmallIntegerField(help_text='mg/dL')
    fasting_blood_sugar = models.PositiveSmallIntegerField(help_text='mg/dL')
    bmi = models.DecimalField(max_digits=5, decimal_places=2)

    smoker = models.BooleanField(default=False)
    diabetic = models.BooleanField(default=False)
    family_history = models.BooleanField(default=False)
    chest_pain = models.BooleanField(default=False)
    sedentary_lifestyle = models.BooleanField(default=False)

    risk_score = models.PositiveSmallIntegerField()
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    summary = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'created_at']),
            models.Index(fields=['risk_level']),
        ]

    def __str__(self):
        return f'Heart risk {self.risk_score}% ({self.risk_level}) for patient {self.patient_id}'
