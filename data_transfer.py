#!/usr/bin/env python
"""
Data transfer script - Export from SQLite, Import to PostgreSQL
"""
import os
import django
import sys
import io

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

django.setup()

from django.core.management import call_command

print("=== Exporting data from SQLite ===")
try:
    with open('data_dump.json', 'w', encoding='utf-8') as f:
        call_command('dumpdata', all=True, indent=2, stdout=f)
    print("✓ Data exported successfully to data_dump.json")
except Exception as e:
    print(f"⚠ Error during export: {e}")
    sys.exit(1)

print(f"✓ Export completed. File size: {os.path.getsize('data_dump.json') / 1024:.2f} KB")
