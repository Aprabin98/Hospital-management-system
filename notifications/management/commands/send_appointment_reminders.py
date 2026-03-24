from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from appointments.models import Appointment
from notifications.models import Notification
from notifications.utils import (
    build_doctor_appointment_whatsapp,
    build_patient_appointment_whatsapp,
    create_notification,
    notify_doctor_whatsapp,
    notify_patient_whatsapp,
)


class Command(BaseCommand):
    help = 'Send reminder notifications for upcoming appointments.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-ahead',
            type=int,
            default=1,
            help='How many days ahead to send reminders for (default: 1).',
        )

    def handle(self, *args, **options):
        days_ahead = options['days_ahead']
        target_date = timezone.localdate() + timedelta(days=days_ahead)

        appointments = Appointment.objects.select_related(
            'patient__user',
            'doctor__user',
        ).filter(
            date=target_date,
            status__in=['PENDING', 'CONFIRMED'],
        )

        sent_count = 0
        skipped_count = 0
        doctor_sent_count = 0
        doctor_skipped_count = 0

        for appointment in appointments:
            action_url = f'/appointments/{appointment.id}/'
            patient_already_sent = Notification.objects.filter(
                recipient=appointment.patient.user,
                title='Appointment Reminder',
                action_url=action_url,
                created_at__date=timezone.localdate(),
            ).exists()
            if patient_already_sent:
                skipped_count += 1
            else:
                create_notification(
                    recipient=appointment.patient.user,
                    title='Appointment Reminder',
                    message=(
                        f"Reminder: You have an appointment with Dr. {appointment.doctor.user.username} "
                        f"on {appointment.date} at {appointment.start_time}. Please arrive 30 minutes early."
                    ),
                    notification_type='APPOINTMENT',
                    action_url=action_url,
                    metadata={'kind': 'appointment_reminder', 'days_ahead': days_ahead},
                )

                notify_patient_whatsapp(
                    appointment.patient,
                    build_patient_appointment_whatsapp(appointment, is_reminder=True),
                )
                sent_count += 1

            doctor_already_sent = Notification.objects.filter(
                recipient=appointment.doctor.user,
                title='Doctor Appointment Reminder',
                action_url=action_url,
                created_at__date=timezone.localdate(),
            ).exists()

            if doctor_already_sent:
                doctor_skipped_count += 1
            else:
                create_notification(
                    recipient=appointment.doctor.user,
                    title='Doctor Appointment Reminder',
                    message=(
                        f"Reminder: Appointment with {appointment.patient.full_name} "
                        f"on {appointment.date} at {appointment.start_time}."
                    ),
                    notification_type='APPOINTMENT',
                    action_url=action_url,
                    metadata={'kind': 'doctor_appointment_reminder', 'days_ahead': days_ahead},
                )
                notify_doctor_whatsapp(
                    appointment.doctor,
                    build_doctor_appointment_whatsapp(appointment, is_reminder=True),
                )
                doctor_sent_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Reminder run complete for {target_date}: sent={sent_count}, skipped={skipped_count}.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Doctor reminders: sent={doctor_sent_count}, skipped={doctor_skipped_count}.'
            )
        )