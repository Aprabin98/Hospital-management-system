from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TestBooking, TestResult, TestResultItem
from notifications.utils import create_notification


@receiver(post_save, sender=TestBooking)
def auto_create_lab_payment(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return

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
    if kwargs.get('raw', False):
        return

    from payments.models import Payment

    payment = Payment.objects.filter(lab_booking=instance).order_by('-created_at').first()
    if not payment:
        return

    next_status = 'PAID' if payment.status == 'PAID' else 'UNPAID'
    if instance.payment_status != next_status:
        instance.payment_status = next_status
        instance.save(update_fields=['payment_status'])


# ===============================================
# LAB RESULT WORKFLOW NOTIFICATIONS
# ===============================================

@receiver(post_save, sender=TestResult)
def notify_on_result_status_change(sender, instance, created, **kwargs):
    """Send notifications when result status changes"""
    if kwargs.get('raw', False):
        return
    
    patient = instance.booking.patient
    booking = instance.booking
    
    # When result entered - notify doctors who ordered this test
    if instance.status == 'ENTERED' and not created:
        # Find doctors who have related appointments/prescriptions
        from appointments.models import Appointment
        doctors = Appointment.objects.filter(
            patient=patient
        ).values_list('doctor__user_id', flat=True).distinct()
        
        for doctor_user_id in doctors:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                doctor_user = User.objects.get(id=doctor_user_id)
                create_notification(
                    recipient=doctor_user,
                    title='Lab Results Ready for Review',
                    message=f'Lab results for {patient.full_name} ({booking.template.name}) are ready for review.',
                    notification_type='LAB',
                )
            except User.DoesNotExist:
                pass
    
    # When result approved by doctor - notify patient
    if instance.status == 'APPROVED':
        if patient.user:
            create_notification(
                recipient=patient.user,
                title='Lab Results Approved',
                message=f'Your {booking.template.name} results have been reviewed and approved by the doctor.',
                notification_type='LAB',
            )
    
    # When result released - notify patient
    if instance.status == 'RELEASED':
        if patient.user:
            create_notification(
                recipient=patient.user,
                title='Lab Results Ready',
                message=f'Your {booking.template.name} results are now available in your health records.',
                notification_type='LAB',
            )


@receiver(post_save, sender=TestResultItem)
def check_critical_values_on_result_item_save(sender, instance, **kwargs):
    """Flag result if critical values detected and notify doctor immediately"""
    if kwargs.get('raw', False):
        return
    
    result = instance.result
    
    # Check if this item is critical
    if instance.is_critical and not result.critical_notification_sent:
        result.has_critical_values = True
        result.critical_notification_sent = True
        result.save(update_fields=['has_critical_values', 'critical_notification_sent'])
        
        # Immediately notify doctor about critical value
        from appointments.models import Appointment
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        doctors = Appointment.objects.filter(
            patient=result.booking.patient
        ).values_list('doctor__user_id', flat=True).distinct()
        
        for doctor_user_id in doctors:
            try:
                doctor_user = User.objects.get(id=doctor_user_id)
                create_notification(
                    recipient=doctor_user,
                    title='⚠️ CRITICAL LAB VALUE DETECTED',
                    message=f'CRITICAL: {instance.field.field_name} = {instance.value} {instance.field.unit} for {result.booking.patient.full_name}. Normal: {instance.field.normal_min}-{instance.field.normal_max}',
                    notification_type='LAB_CRITICAL',
                )
            except User.DoesNotExist:
                pass