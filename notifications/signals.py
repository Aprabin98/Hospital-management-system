from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from appointments.models import Appointment
from lab.models import TestResult
from payments.models import Payment

from .utils import (
    build_doctor_appointment_whatsapp,
    build_patient_appointment_whatsapp,
    build_patient_status_whatsapp,
    create_notification,
    notify_doctor_whatsapp,
    notify_patient_whatsapp,
)


@receiver(pre_save, sender=Appointment)
def _capture_appointment_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = Appointment.objects.get(pk=instance.pk).status
        except Appointment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Appointment)
def on_appointment_saved(sender, instance, created, **kwargs):
    if created:
        create_notification(
            recipient=instance.patient.user,
            title='Appointment Confirmed',
            message=(
                f'Your appointment with Dr. {instance.doctor.user.username} is confirmed '
                f'for {instance.date} at {instance.start_time}. Please arrive 30 minutes early.'
            ),
            notification_type='APPOINTMENT',
            action_url=f'/appointments/{instance.id}/',
        )
        notify_patient_whatsapp(
            instance.patient,
            build_patient_appointment_whatsapp(instance, is_reminder=False),
        )
        create_notification(
            recipient=instance.doctor.user,
            title='New Appointment',
            message=f'New appointment booked by {instance.patient.full_name} for {instance.date} at {instance.start_time}.',
            notification_type='APPOINTMENT',
            action_url=f'/appointments/{instance.id}/',
        )
        notify_doctor_whatsapp(
            instance.doctor,
            build_doctor_appointment_whatsapp(instance, is_reminder=False),
        )
        return

    old_status = getattr(instance, '_old_status', None)
    if old_status != instance.status:
        create_notification(
            recipient=instance.patient.user,
            title='Appointment Status Updated',
            message=f'Your appointment status is now {instance.get_status_display()}.',
            notification_type='APPOINTMENT',
            action_url=f'/appointments/{instance.id}/',
            metadata={'old_status': old_status, 'new_status': instance.status},
        )
        notify_patient_whatsapp(instance.patient, build_patient_status_whatsapp(instance))

        create_notification(
            recipient=instance.doctor.user,
            title='Appointment Status Updated',
            message=(
                f'Appointment for {instance.patient.full_name} is now '
                f'{instance.get_status_display()}.'
            ),
            notification_type='APPOINTMENT',
            action_url=f'/appointments/{instance.id}/',
            metadata={'old_status': old_status, 'new_status': instance.status},
        )


@receiver(pre_save, sender=Payment)
def _capture_payment_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = Payment.objects.get(pk=instance.pk).status
        except Payment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Payment)
def on_payment_saved(sender, instance, created, **kwargs):
    old_status = getattr(instance, '_old_status', None)
    if created:
        return

    if old_status != 'PAID' and instance.status == 'PAID':
        create_notification(
            recipient=instance.patient.user,
            title='Payment Received',
            message=f'Payment of Rs. {instance.amount} has been marked as paid.',
            notification_type='PAYMENT',
            action_url=f'/payments/{instance.id}/',
        )


@receiver(pre_save, sender=TestResult)
def _capture_result_release(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_released = TestResult.objects.get(pk=instance.pk).is_released
        except TestResult.DoesNotExist:
            instance._old_released = False
    else:
        instance._old_released = False


@receiver(post_save, sender=TestResult)
def on_result_saved(sender, instance, created, **kwargs):
    old_released = getattr(instance, '_old_released', False)
    if not old_released and instance.is_released:
        create_notification(
            recipient=instance.booking.patient.user,
            title='Lab Report Released',
            message=f'Your {instance.booking.template.name} report is now available.',
            notification_type='LAB',
            action_url=f'/lab/bookings/{instance.booking.id}/',
        )
        notify_patient_whatsapp(
            instance.booking.patient,
            (
                f"HMS: Your lab report for {instance.booking.template.name} is now available. "
                f"Please check your HMS account."
            ),
        )
