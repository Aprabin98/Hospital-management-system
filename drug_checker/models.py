from django.conf import settings
from django.db import models


class DrugInteraction(models.Model):
    SEVERITY_MINOR = 'MINOR'
    SEVERITY_MODERATE = 'MODERATE'
    SEVERITY_MAJOR = 'MAJOR'
    SEVERITY_CONTRAINDICATED = 'CONTRAINDICATED'

    SEVERITY_CHOICES = [
        (SEVERITY_MINOR, 'Minor'),
        (SEVERITY_MODERATE, 'Moderate'),
        (SEVERITY_MAJOR, 'Major'),
        (SEVERITY_CONTRAINDICATED, 'Contraindicated'),
    ]

    drug_a = models.CharField(max_length=200)
    drug_b = models.CharField(max_length=200)
    drug_a_normalized = models.CharField(max_length=200, db_index=True)
    drug_b_normalized = models.CharField(max_length=200, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MODERATE)
    description = models.TextField(blank=True)
    management = models.TextField(blank=True)
    source = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['drug_a_normalized', 'drug_b_normalized']),
            models.Index(fields=['severity']),
        ]
        unique_together = ('drug_a_normalized', 'drug_b_normalized')

    def save(self, *args, **kwargs):
        self.drug_a_normalized = (self.drug_a or '').strip().lower()
        self.drug_b_normalized = (self.drug_b or '').strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.drug_a} + {self.drug_b} ({self.severity})'


class InteractionCheckLog(models.Model):
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drug_interaction_checks',
    )
    medicines = models.JSONField(default=list)
    interactions_found = models.PositiveIntegerField(default=0)
    worst_severity = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Check by {self.checked_by_id} ({self.interactions_found} found)'
