#!/usr/bin/env python
"""
Create a clean data dump excluding Django built-in tables
"""
import os
import django
import sys
import io

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Temporarily switch to SQLite
import hms_project.settings as settings_module
settings_module.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite3'),
    }
}

django.setup()

from django.core.management import call_command

# Apps that contain actual HMS data (exclude Django built-ins)
app_list = [
    'users',
    'clinical',
    'appointments',
    'prescriptions',
    'lab',
    'payments',
    'rooms',
    'reviews',
    'notifications',
]

print("=== Creating clean data dump (HMS apps only) ===")
try:
    with open('data_dump_hms_only.json', 'w', encoding='utf-8') as f:
        call_command('dumpdata', *app_list, indent=2, stdout=f)
    print("✓ Clean dump created: data_dump_hms_only.json")
    print(f"✓ File size: {os.path.getsize('data_dump_hms_only.json') / 1024:.2f} KB")
except Exception as e:
    print(f"⚠ Error: {e}")
    sys.exit(1)
