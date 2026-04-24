"""Seed initial radiology imaging catalog records for QA.
Run with: python seed_radiology_data.py
"""
import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

call_command('migrate', interactive=False, verbosity=0)

from radiology.models import ImagingCatalog

CATALOG_ITEMS = [
    {
        'name': 'Chest X-Ray PA View',
        'modality': 'XRAY',
        'description': 'Standard chest radiograph for cough, fever, and chest symptoms.',
        'preparation': 'Remove metal objects and wear a radiology gown.',
        'price': 900,
        'turnaround_hours': 4,
    },
    {
        'name': 'CT Head Without Contrast',
        'modality': 'CT',
        'description': 'Rapid brain imaging for trauma, stroke, and acute neurological complaints.',
        'preparation': 'No specific preparation unless instructed by the radiology team.',
        'price': 6500,
        'turnaround_hours': 6,
    },
    {
        'name': 'MRI Brain With Contrast',
        'modality': 'MRI',
        'description': 'Detailed brain imaging for neurology and mass evaluation workflows.',
        'preparation': 'Screen for metal implants before booking the study.',
        'price': 12500,
        'turnaround_hours': 12,
    },
    {
        'name': 'Ultrasound Abdomen',
        'modality': 'USG',
        'description': 'Abdominal ultrasound for hepatobiliary, renal, and pelvic assessment.',
        'preparation': 'Fast for 6 to 8 hours before the study when possible.',
        'price': 3200,
        'turnaround_hours': 3,
    },
]

created_count = 0
for item in CATALOG_ITEMS:
    _, created = ImagingCatalog.objects.get_or_create(
        name=item['name'],
        defaults=item,
    )
    if created:
        created_count += 1

print(f'Radiology catalog ready. Created {created_count} new items; total items: {ImagingCatalog.objects.count()}')
