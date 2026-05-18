"""
Force-delete users with email ending @hms.test by temporarily disabling sqlite foreign key checks.
USE ONLY AFTER DB BACKUP
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from django.db import connection

sqls = [
    "PRAGMA foreign_keys = OFF;",
    "DELETE FROM users_user WHERE email LIKE '%@hms.test';",
    "DELETE FROM users_user_groups WHERE user_id NOT IN (SELECT id FROM users_user);",
    "DELETE FROM users_user_user_permissions WHERE user_id NOT IN (SELECT id FROM users_user);",
    "PRAGMA foreign_keys = ON;",
]

with connection.cursor() as cur:
    for s in sqls:
        print('EXEC:', s)
        cur.execute(s)

# Verify
with connection.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM users_user WHERE email LIKE '%@hms.test';")
    remaining = cur.fetchone()[0]
    print('REMAINING_SEEDED_USERS', remaining)
    cur.execute("SELECT COUNT(*) FROM users_user;")
    total = cur.fetchone()[0]
    print('TOTAL_USERS_AFTER', total)
