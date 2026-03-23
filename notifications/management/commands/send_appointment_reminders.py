from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from appointments.models import Appointment
from notifications.models import Notification
from notifications.utils import create_notification, notify_patient_whatsapp


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

        for appointment in appointments:
            action_url = f'/appointments/{appointment.id}/'
            already_sent = Notification.objects.filter(
                recipient=appointment.patient.user,
                title='Appointment Reminder',
                action_url=action_url,
                created_at__date=timezone.localdate(),
            ).exists()
            if already_sent:
                skipped_count += 1
                continue

            create_notification(
                recipient=appointment.patient.user,
                title='Appointment Reminder',
                message=(
                    f"Reminder: You have an appointment with Dr. {appointment.doctor.user.username} "
                    f"on {appointment.date} at {appointment.start_time}."
                ),
                notification_type='APPOINTMENT',
                action_url=action_url,
                metadata={'kind': 'appointment_reminder', 'days_ahead': days_ahead},
            )

            notify_patient_whatsapp(
                appointment.patient,
                (
                    f"HMS Reminder: Appointment with Dr. {appointment.doctor.user.username} "
                    f"on {appointment.date} at {appointment.start_time}."
                ),
            )
            sent_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Reminder run complete for {target_date}: sent={sent_count}, skipped={skipped_count}.'
            )
        )