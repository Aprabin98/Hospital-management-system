"""
Audit script: lists DB tables not managed by Django models and seeded users (@hms.test)
Run with: python audit_db.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from django.db import connection
from django.apps import apps

print('EXTRA_TABLES_START')
try:
    tables = set(connection.introspection.table_names())
    model_tables = {m._meta.db_table for m in apps.get_models() if m._meta.managed}
    extras = sorted(tables - model_tables)
    for t in extras:
        print(t)
except Exception as e:
    print('ERROR_INSPECTING_TABLES', str(e))
print('EXTRA_TABLES_END')

print('SEED_USERS_START')
try:
    from users.models import User
    qs = User.objects.filter(email__iendswith='@hms.test').order_by('id')
    for u in qs:
        print(f'{u.id}|{u.email}|{u.role}|staff={u.is_staff}|super={u.is_superuser}')
except Exception as e:
    print('ERROR_LISTING_USERS', str(e))
print('SEED_USERS_END')

try:
    from users.models import User
    print('TOTAL_USERS', User.objects.count())
except Exception:
    pass
