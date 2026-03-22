from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from lab.models import TestBooking
from .models import Payment


@receiver(post_save, sender=Appointment)
def auto_create_appointment_payment(sender, instance, created, **kwargs):
    if instance.status == 'CONFIRMED':
        Payment.objects.get_or_create(
            appointment=instance,
            payment_type='APPOINTMENT',
            defaults={
                'patient': instance.patient,
                'doctor': instance.doctor,
                'amount': instance.doctor.consultation_fee,
                'status': 'UNPAID',
            }
        )


@receiver(post_save, sender=TestBooking)
def auto_create_lab_payment(sender, instance, created, **kwargs):
    if created:
        Payment.objects.get_or_create(
            lab_booking=instance,
            payment_type='LAB_TEST',
            defaults={
                'patient': instance.patient,
                'amount': instance.amount,
                'status': 'UNPAID',
            }
        )


@receiver(post_save, sender=Payment)
def sync_lab_booking_payment_status(sender, instance, **kwargs):
    if not instance.lab_booking_id:
        return

    next_status = 'PAID' if instance.status == 'PAID' else 'UNPAID'
    booking = instance.lab_booking
    if booking.payment_status != next_status:
        booking.payment_status = next_status
        booking.save(update_fields=['payment_status'])