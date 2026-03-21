from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ('GENERAL', 'General'),
        ('APPOINTMENT', 'Appointment'),
        ('PAYMENT', 'Payment'),
        ('LAB', 'Lab'),
        ('PRESCRIPTION', 'Prescription'),
        ('ROOM', 'Room'),
        ('SECURITY', 'Security'),
    ]

    recipient = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='GENERAL')
    action_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"
