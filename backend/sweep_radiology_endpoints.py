"""Targeted radiology endpoint sweep.
Runs a small authenticated smoke sweep for the new radiology routes and appends a summary to the consolidated regression report.
"""
import os
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')

import django
from django.core.management import call_command

django.setup()

call_command('migrate', interactive=False, verbosity=0)

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from clinical.models import Doctor, Specialization
from radiology.models import ImagingCatalog, ImagingOrder, ImagingReport
from users.models import PatientProfile

REPORT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ENDPOINT_REGRESSION_REPORT.md'))


def ensure_user(email, username, role):
    User = get_user_model()
    user = User.objects.filter(email=email).first()
    if not user:
        user = User.objects.create_user(
            email=email,
            username=username,
            password=None,
            role=role,
            is_active=True,
        )
    else:
        updated_fields = []
        if user.username != username:
            user.username = username
            updated_fields.append('username')
        if user.role != role:
            user.role = role
            updated_fields.append('role')
        if not user.is_active:
            user.is_active = True
            updated_fields.append('is_active')
        if updated_fields:
            user.save(update_fields=updated_fields)
    return user


def ensure_doctor(user):
    specialization, _ = Specialization.objects.get_or_create(
        name='Radiology',
        defaults={'description': 'Radiology and imaging'}
    )
    doctor, _ = Doctor.objects.get_or_create(
        user=user,
        defaults={
            'specialization': specialization,
            'consultation_fee': 0,
            'experience_years': 5,
            'is_available': True,
        },
    )
    if doctor.specialization_id != specialization.id:
        doctor.specialization = specialization
        doctor.save(update_fields=['specialization'])
    return doctor


def ensure_patient(user, full_name):
    patient, _ = PatientProfile.objects.get_or_create(
        user=user,
        defaults={'full_name': full_name},
    )
    if not patient.full_name:
        patient.full_name = full_name
        patient.save(update_fields=['full_name'])
    return patient


def ensure_catalog():
    items = [
        ('Chest X-Ray PA View', 'XRAY', 'Standard chest radiograph for cough, fever, and chest symptoms.', 'Remove metal objects and wear a radiology gown.', 900),
        ('CT Head Without Contrast', 'CT', 'Rapid brain imaging for trauma, stroke, and acute neurological complaints.', 'No specific preparation unless instructed by the radiology team.', 6500),
        ('MRI Brain With Contrast', 'MRI', 'Detailed brain imaging for neurology and mass evaluation workflows.', 'Screen for metal implants before booking the study.', 12500),
    ]
    catalog_items = []
    for name, modality, description, preparation, price in items:
        catalog, _ = ImagingCatalog.objects.get_or_create(
            name=name,
            defaults={
                'modality': modality,
                'description': description,
                'preparation': preparation,
                'price': price,
                'turnaround_hours': 6,
                'is_active': True,
            },
        )
        catalog_items.append(catalog)
    return catalog_items


admin_user = ensure_user('radiology.admin@example.com', 'radiology_admin', 'ADMIN')
doctor_user = ensure_user('radiology.doctor@example.com', 'radiology_doctor', 'DOCTOR')
patient_user = ensure_user('radiology.patient@example.com', 'radiology_patient', 'PATIENT')
other_patient_user = ensure_user('radiology.other@example.com', 'radiology_other', 'PATIENT')

ensure_doctor(doctor_user)
patient = ensure_patient(patient_user, 'Radiology Patient')
other_patient = ensure_patient(other_patient_user, 'Other Radiology Patient')

catalog_items = ensure_catalog()
order, _ = ImagingOrder.objects.get_or_create(
    patient=patient,
    catalog_item=catalog_items[0],
    defaults={
        'ordered_by': doctor_user,
        'priority': 'URGENT',
        'status': 'ORDERED',
        'clinical_notes': 'Initial QA imaging order',
    },
)
ImagingOrder.objects.get_or_create(
    patient=other_patient,
    catalog_item=catalog_items[1],
    defaults={
        'ordered_by': doctor_user,
        'priority': 'ROUTINE',
        'status': 'ORDERED',
        'clinical_notes': 'Second QA order',
    },
)

client = APIClient()
results = []


def record(name, response, expect_status):
    ok = response.status_code == expect_status
    results.append({
        'name': name,
        'status': response.status_code,
        'expected': expect_status,
        'ok': ok,
        'detail': response.data if hasattr(response, 'data') else response.content.decode('utf-8', errors='ignore'),
    })


# Role access: patient cannot release a report.
client.force_authenticate(user=patient_user)
response = client.post(reverse('radiology:order_release', args=[order.id]), {}, format='json')
record('patient_cannot_release_report', response, 403)

# Catalog access for staff.
client.force_authenticate(user=doctor_user)
response = client.get(reverse('radiology:catalog_list_create'))
record('doctor_can_view_catalog', response, 200)

# Orders worklist access.
response = client.get(reverse('radiology:orders_list_create'))
record('doctor_can_view_orders', response, 200)

# Report release flow.
report, _ = ImagingReport.objects.get_or_create(order=order)
response = client.put(
    reverse('radiology:order_report', args=[order.id]),
    {
        'findings': 'Mild bibasal haziness.',
        'impression': 'Possible early infective change.',
        'recommendation': 'Clinical correlation advised.',
        'report_status': 'FINAL',
        'is_critical': False,
    },
    format='json',
)
record('doctor_can_save_report', response, 200)

response = client.post(reverse('radiology:order_release', args=[order.id]), {}, format='json')
record('doctor_can_release_report', response, 200)

# History visibility.
client.force_authenticate(user=patient_user)
response = client.get(reverse('radiology:history'))
record('patient_can_view_own_history', response, 200)

client.force_authenticate(user=doctor_user)
response = client.get(f"{reverse('radiology:history')}?patient_id={patient.id}")
record('doctor_can_view_patient_history', response, 200)

# Build summary.
passed = sum(1 for item in results if item['ok'])
failed = len(results) - passed
summary_line = f"- Sweep results: {passed}/{len(results)} passed, {failed} failed"

section_lines = [
    '',
    '## Radiology Endpoint Sweep Appendix',
    '',
    f'Generated at: {datetime.now().isoformat()}',
    '',
    summary_line,
    '',
    '| Check | Expected | Actual | Result |',
    '|---|---|---|---|',
]
for item in results:
    result = 'PASS' if item['ok'] else 'FAIL'
    section_lines.append(f"| {item['name']} | {item['expected']} | {item['status']} | {result} |")

section_lines.extend([
    '',
    '### Notes',
    '- Patient history is restricted to the authenticated patient\'s released studies.',
    '- Staff history access requires a `patient_id` scope parameter.',
    '- Release flow updates both the order and the embedded report record.',
])

with open(REPORT_PATH, 'r', encoding='utf-8') as handle:
    current_report = handle.read().rstrip()

with open(REPORT_PATH, 'w', encoding='utf-8') as handle:
    handle.write(current_report)
    handle.write('\n')
    handle.write('\n'.join(section_lines))
    handle.write('\n')

print(summary_line)
for item in results:
    print(f"{item['name']}: {item['status']} (expected {item['expected']})")
