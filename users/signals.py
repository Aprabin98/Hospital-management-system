from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, PatientProfile


@receiver(post_save, sender=User)
def create_patient_profile(sender, instance, created, **kwargs):
    """Auto-create PatientProfile when a PATIENT user is created."""
    if created and instance.role == 'PATIENT':
        PatientProfile.objects.create(
            user=instance,
            full_name=instance.username
        )


@receiver(post_save, sender=User)
def save_patient_profile(sender, instance, **kwargs):
    """Save PatientProfile when User is saved."""
    if instance.role == 'PATIENT':
        try:
            instance.patient_profile.save()
        except PatientProfile.DoesNotExist:
            PatientProfile.objects.create(
                user=instance,
                full_name=instance.username
            )