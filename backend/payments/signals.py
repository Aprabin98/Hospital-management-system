from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment
from lab.models import TestBooking
from .models import Payment, PaymentReminder, PaymentReminderLog
from notifications.utils import create_notification


@receiver(post_save, sender=Appointment)
def auto_create_appointment_payment(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return

    # Create payment when appointment is first created (regardless of status)
    if created:
        payment, created = Payment.objects.get_or_create(
            appointment=instance,
            payment_type='APPOINTMENT',
            defaults={
                'patient': instance.patient,
                'doctor': instance.doctor,
                'amount': instance.doctor.consultation_fee,
                'status': 'UNPAID',
                'due_date': instance.date,  # Set due date to appointment date
            }
        )
        
        # Auto-create reminder for new payment
        if created:
            PaymentReminder.objects.get_or_create(
                payment=payment,
                defaults={'is_active': True}
            )


@receiver(post_save, sender=TestBooking)
def auto_create_lab_payment(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return

    if created:
        payment, created = Payment.objects.get_or_create(
            lab_booking=instance,
            payment_type='LAB_TEST',
            defaults={
                'patient': instance.patient,
                'amount': instance.amount,
                'status': 'UNPAID',
                'due_date': instance.date + timedelta(days=7),  # 7 days to pay
            }
        )
        
        # Auto-create reminder for new payment
        if created:
            PaymentReminder.objects.get_or_create(
                payment=payment,
                defaults={'is_active': True}
            )


@receiver(post_save, sender=Payment)
def sync_lab_booking_payment_status(sender, instance, **kwargs):
    if kwargs.get('raw', False):
        return

    if not instance.lab_booking_id:
        return

    instance.lab_booking.payment_status = 'PAID' if instance.status == 'PAID' else 'UNPAID'
    instance.lab_booking.save(update_fields=['payment_status'])


@receiver(post_save, sender=Payment)
def auto_create_payment_reminder(sender, instance, created, **kwargs):
    """Auto-create reminder when payment is created"""
    if kwargs.get('raw', False):
        return
    
    if created and instance.status == 'UNPAID':
        PaymentReminder.objects.get_or_create(
            payment=instance,
            defaults={'is_active': True}
        )


@receiver(post_save, sender=Payment)
def notify_on_payment_status_change(sender, instance, created, **kwargs):
    """Send notifications when payment is made"""
    if kwargs.get('raw', False):
        return
    
    if not created and instance.status == 'PAID':
        # Payment just completed
        patient = instance.patient
        if patient.user:
            create_notification(
                recipient=patient.user,
                title='Payment Received',
                message=f'Your payment of Rs.{instance.amount} has been received successfully. Receipt: #{instance.id}',
                notification_type='PAYMENT',
            )
        
        # Disable reminders since payment is complete
        try:
            reminder = instance.reminder
            reminder.is_active = False
            reminder.save(update_fields=['is_active'])
        except PaymentReminder.DoesNotExist:
            pass


# ===============================================
# PAYMENT REMINDER SENDING SIGNALS
# ===============================================

@receiver(post_save, sender=PaymentReminder)
def send_payment_reminders_on_schedule(sender, instance, **kwargs):
    """Automatically send payment reminders based on schedule"""
    if kwargs.get('raw', False) or not instance.is_active:
        return
    
    payment = instance.payment
    
    # Check and send first reminder
    if instance.should_send_first_reminder():
        _send_payment_reminder(payment, instance, reminder_number=1)
        instance.first_reminder_sent = True
        instance.first_reminder_sent_at = timezone.now()
        instance.save(update_fields=['first_reminder_sent', 'first_reminder_sent_at'])
    
    # Check and send second reminder
    if instance.should_send_second_reminder():
        _send_payment_reminder(payment, instance, reminder_number=2)
        instance.second_reminder_sent = True
        instance.second_reminder_sent_at = timezone.now()
        instance.save(update_fields=['second_reminder_sent', 'second_reminder_sent_at'])
    
    # Check and send final reminder
    if instance.should_send_final_reminder():
        _send_payment_reminder(payment, instance, reminder_number=3)
        instance.final_reminder_sent = True
        instance.final_reminder_sent_at = timezone.now()
        instance.save(update_fields=['final_reminder_sent', 'final_reminder_sent_at'])


def _send_payment_reminder(payment, reminder, reminder_number):
    """Helper function to send payment reminder via multiple channels"""
    patient = payment.patient
    
    if not patient.user:
        return
    
    # Build reminder message
    amount_remaining = payment.amount - payment.amount_paid
    days_overdue = (timezone.now().date() - payment.due_date).days if payment.due_date else 0
    
    if reminder_number == 1:
        subject = f"Payment Reminder: Rs.{amount_remaining} Due Soon"
        message = f"Your payment of Rs.{amount_remaining} is due on {payment.due_date}. Please complete payment to avoid late fees."
    elif reminder_number == 2:
        subject = f"Payment Overdue: Rs.{amount_remaining} ({days_overdue} days late)"
        message = f"Your payment of Rs.{amount_remaining} is now {days_overdue} days overdue. Please make payment immediately."
    else:  # final
        subject = f"FINAL NOTICE: Payment Required - Rs.{amount_remaining} ({days_overdue} days overdue)"
        message = f"URGENT: Your payment of Rs.{amount_remaining} is {days_overdue} days overdue. Contact hospital to arrange payment."
    
    # Send via in-app notification
    create_notification(
        recipient=patient.user,
        title=subject,
        message=message,
        notification_type='PAYMENT_REMINDER',
    )
    
    # Log the reminder
    PaymentReminderLog.objects.create(
        reminder=reminder,
        payment=payment,
        reminder_number=reminder_number,
        channel='IN_APP',
        recipient=patient.user.email,
        status='SENT',
        message_preview=message,
    )
    
    # Update payment tracking
    payment.reminder_sent_count += 1
    payment.last_reminder_sent = timezone.now()
    payment.save(update_fields=['reminder_sent_count', 'last_reminder_sent'])


    next_status = 'PAID' if instance.status == 'PAID' else 'UNPAID'
    try:
        booking = instance.lab_booking
    except TestBooking.DoesNotExist:
        return

    if booking.payment_status != next_status:
        booking.payment_status = next_status
        booking.save(update_fields=['payment_status'])