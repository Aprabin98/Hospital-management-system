"""
Safer deletion: for each seeded user, inspect related objects, delete blocking relations, then delete user.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db import models
from users.models import User

seed_qs = User.objects.filter(email__iendswith='@hms.test').order_by('id')
print('FOUND', seed_qs.count())

for u in seed_qs:
    print('\nPROCESSING', u.id, u.email)
    blockers = []
    # Inspect related objects
    for rel in u._meta.related_objects:
        accessor = rel.get_accessor_name()
        try:
            manager = getattr(u, accessor)
        except AttributeError:
            continue
        try:
            count = manager.count()
        except Exception:
            # fallback
            try:
                count = len(list(manager.all()))
            except Exception:
                count = None
        on_delete = None
        try:
            on_delete = rel.field.remote_field.on_delete
        except Exception:
            on_delete = None
        print('  REL', accessor, 'count=', count, 'on_delete=', getattr(on_delete, '__name__', str(on_delete)))
        if count:
            # If protected, delete related objects first
            if on_delete == models.PROTECT or getattr(on_delete, '__name__', '') == 'PROTECT':
                print('    -> Deleting protected related objects:', accessor)
                try:
                    manager.all().delete()
                except Exception as e:
                    print('    !! Failed to delete related objects:', e)
                    blockers.append((accessor, str(e)))
            else:
                # Try letting cascade happen, but note it
                print('    -> Will attempt cascade delete (or set_null)')
    if blockers:
        print('  BLOCKERS FOUND, SKIPPING DELETE:', blockers)
        continue
    # Try deleting user
    try:
        with transaction.atomic():
            u.delete()
        print('  DELETED', u.email)
    except ProtectedError as pe:
        print('  ProtectedError:', pe)
    except Exception as e:
        print('  DELETE_FAILED', e)

print('\nDONE')
