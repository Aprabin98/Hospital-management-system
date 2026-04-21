from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('SECURITY', 'Security'),
        ('OTHER', 'Other'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    actor_email = models.EmailField(blank=True)
    actor_role = models.CharField(max_length=30, blank=True)

    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='OTHER')
    model_name = models.CharField(max_length=120, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)

    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    path = models.CharField(max_length=255, blank=True)
    method = models.CharField(max_length=10, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['model_name']),
        ]

    def __str__(self):
        actor = self.actor_email or 'Anonymous'
        target = self.object_repr or self.model_name or 'N/A'
        return f'{self.action} by {actor} on {target}'


class SystemSetting(models.Model):
    hospital_name = models.CharField(max_length=255, default='Hospital Management System')
    hospital_email = models.EmailField(default='admin@hospital.com')
    hospital_phone = models.CharField(max_length=64, default='+91-XXXXXXXXXX')
    hospital_address = models.TextField(default='123 Medical Street, City')

    max_appointments_per_day = models.PositiveIntegerField(default=50)
    appointment_slot_duration = models.PositiveIntegerField(default=30)
    cancellation_notice_hours = models.PositiveIntegerField(default=2)
    max_concurrent_users = models.PositiveIntegerField(default=100)

    maintenance_mode = models.BooleanField(default=False)
    auto_backup_enabled = models.BooleanField(default=True)
    backup_frequency_days = models.PositiveIntegerField(default=1)
    enable_two_factor = models.BooleanField(default=True)
    enable_notifications = models.BooleanField(default=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_settings_updates',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return f'System Settings #{self.pk}'
