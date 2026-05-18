"""
Delete seeded users whose emails end with @hms.test
Run with: python delete_seeded_users.py
This will delete users and cascade related profiles where on_delete=CASCADE.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from django.db import transaction

from users.models import User

seed_qs = User.objects.filter(email__iendswith='@hms.test')
print('TO_DELETE_COUNT', seed_qs.count())
for u in seed_qs.order_by('id'):
    print(f'DELETE_PREVIEW {u.id}|{u.email}|{u.role}|staff={u.is_staff}|super={u.is_superuser}')

if seed_qs.exists():
    confirm = True
    if confirm:
        with transaction.atomic():
            deleted_info = seed_qs.delete()
        print('DELETED', deleted_info)
    else:
        print('ABORTED')
else:
    print('NO_SEEDED_USERS_FOUND')
