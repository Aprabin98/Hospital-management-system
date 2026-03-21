from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TestBooking

@receiver(post_save, sender=TestBooking)
def auto_create_lab_payment(sender, instance, created, **kwargs):
    if created:
        from payments.models import Payment
        # We need a separate model for lab payments
        # OR reuse existing payment with a type field