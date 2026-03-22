#!/usr/bin/env python
"""
Smart data loader - removes conflicting content types before loading
"""
import json
import os
import django
import sys
import io

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

django.setup()

# Load and clean the dump file
with open('data_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter out Django's built-in content types (we'll regenerate them)
filtered_data = []
problematic_models = ['contenttypes.ContentType']
skipped_count = 0

for item in data:
    model = item.get('model', '')
    if model not in problematic_models:
        filtered_data.append(item)
    else:
        skipped_count += 1

# Save cleaned data
with open('data_dump_clean.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, indent=2)

print(f"✓ Cleaned dump file created")
print(f"  - Original items: {len(data)}")
print(f"  - Skipped items: {skipped_count}")
print(f"  - Items to load: {len(filtered_data)}")

# Now load the cleaned data
from django.core.management import call_command

print("\n=== Loading data into PostgreSQL ===")
try:
    call_command('loaddata', 'data_dump_clean.json')
    print("✓ Data loaded successfully!")
except Exception as e:
    print(f"⚠ Error during load: {e}")
    sys.exit(1)
