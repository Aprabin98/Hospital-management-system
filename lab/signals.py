from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TestBooking

@receiver(post_save, sender=TestBooking)
def auto_create_lab_payment(sender, instance, created, **kwargs):
    if created:
        from payments.models import Payment
        # Use shared payment model with LAB_TEST type.
        Payment.objects.get_or_create(
            lab_booking=instance,
            payment_type='LAB_TEST',
            defaults={
                'patient': instance.patient,
                'amount': instance.amount,
                'status': 'UNPAID',
            }
        )


@receiver(post_save, sender=TestBooking)
def sync_lab_booking_payment_status(sender, instance, **kwargs):
    from payments.models import Payment

    payment = Payment.objects.filter(lab_booking=instance).order_by('-created_at').first()
    if not payment:
        return

    next_status = 'PAID' if payment.status == 'PAID' else 'UNPAID'
    if instance.payment_status != next_status:
        instance.payment_status = next_status
        instance.save(update_fields=['payment_status'])