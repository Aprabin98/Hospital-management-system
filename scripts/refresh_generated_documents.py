import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')

import django

django.setup()

from django.conf import settings
from appointments.models import Appointment
from prescriptions.models import Prescription
from payments.models import Payment
from lab.models import TestResult


def clear_directory(relative_path):
    target = os.path.join(settings.MEDIA_ROOT, relative_path)
    if os.path.isdir(target):
        for name in os.listdir(target):
            path = os.path.join(target, name)
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)


Appointment.objects.exclude(pdf_file='').update(pdf_file=None)
Appointment.objects.exclude(qr_code='').update(qr_code=None)
Prescription.objects.exclude(pdf_file='').update(pdf_file=None)
Payment.objects.exclude(receipt_file='').update(receipt_file=None)
TestResult.objects.exclude(pdf_file='').update(pdf_file=None)

clear_directory('appointments/pdfs')
clear_directory('appointments/qrcodes')
clear_directory('prescriptions/pdfs')
clear_directory('payments/receipts')
clear_directory('lab/reports')

print('Old generated documents cleared. New downloads will regenerate with updated templates.')
