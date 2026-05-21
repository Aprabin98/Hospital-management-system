from datetime import time

from django.core.management.base import BaseCommand

from lab.models import TestSchedule, TestTemplate


SCHEDULE_PLAN = {
    'blood sugar': [
        ('MON', time(6, 0), time(8, 0)),
        ('TUE', time(6, 0), time(8, 0)),
        ('WED', time(6, 0), time(8, 0)),
        ('THU', time(6, 0), time(8, 0)),
        ('FRI', time(6, 0), time(8, 0)),
    ],
    'blood sugar test': [
        ('MON', time(6, 0), time(8, 0)),
        ('TUE', time(6, 0), time(8, 0)),
        ('WED', time(6, 0), time(8, 0)),
        ('THU', time(6, 0), time(8, 0)),
        ('FRI', time(6, 0), time(8, 0)),
        ('SAT', time(7, 0), time(9, 0)),
    ],
    'cbc': [
        ('MON', time(8, 0), time(12, 0)),
        ('TUE', time(8, 0), time(12, 0)),
        ('WED', time(8, 0), time(12, 0)),
        ('THU', time(8, 0), time(12, 0)),
        ('FRI', time(8, 0), time(12, 0)),
        ('SAT', time(8, 0), time(12, 0)),
    ],
    'lipid profile': [
        ('MON', time(7, 0), time(10, 0)),
        ('TUE', time(7, 0), time(10, 0)),
        ('WED', time(7, 0), time(10, 0)),
        ('THU', time(7, 0), time(10, 0)),
        ('FRI', time(7, 0), time(10, 0)),
        ('SAT', time(7, 0), time(10, 0)),
    ],
    'liver function': [
        ('MON', time(8, 0), time(12, 0)),
        ('TUE', time(8, 0), time(12, 0)),
        ('WED', time(8, 0), time(12, 0)),
        ('THU', time(8, 0), time(12, 0)),
        ('FRI', time(8, 0), time(12, 0)),
        ('SAT', time(8, 0), time(12, 0)),
    ],
    'thyroid profile': [
        ('MON', time(8, 0), time(11, 0)),
        ('TUE', time(8, 0), time(11, 0)),
        ('WED', time(8, 0), time(11, 0)),
        ('THU', time(8, 0), time(11, 0)),
        ('FRI', time(8, 0), time(11, 0)),
    ],
    'ecg': [
        ('MON', time(9, 0), time(17, 0)),
        ('TUE', time(9, 0), time(17, 0)),
        ('WED', time(9, 0), time(17, 0)),
        ('THU', time(9, 0), time(17, 0)),
        ('FRI', time(9, 0), time(17, 0)),
        ('SAT', time(9, 0), time(13, 0)),
        ('SUN', time(10, 0), time(12, 0)),
    ],
}


class Command(BaseCommand):
    help = 'Seed weekday availability for lab tests.'

    def handle(self, *args, **options):
        updated = 0

        for template in TestTemplate.objects.all():
            plan = SCHEDULE_PLAN.get(template.name.strip().lower())
            if not plan:
                plan = [
                    ('MON', time(8, 0), time(12, 0)),
                    ('TUE', time(8, 0), time(12, 0)),
                    ('WED', time(8, 0), time(12, 0)),
                    ('THU', time(8, 0), time(12, 0)),
                    ('FRI', time(8, 0), time(12, 0)),
                ]

            for day, start_time, end_time in plan:
                schedule, created = TestSchedule.objects.update_or_create(
                    template=template,
                    day=day,
                    defaults={
                        'start_time': start_time,
                        'end_time': end_time,
                        'max_bookings': 20,
                        'is_active': True,
                    },
                )
                updated += 1
                action = 'CREATED' if created else 'UPDATED'
                self.stdout.write(f'{action} {template.name} {schedule.get_day_display()} {start_time}-{end_time}')

        self.stdout.write(self.style.SUCCESS(f'Availability seeded for {updated} schedule rows.'))