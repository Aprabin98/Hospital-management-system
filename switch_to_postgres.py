#!/usr/bin/env python
"""Switch back to PostgreSQL and load data"""
import re

# Read the settings file
with open('hms_project/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace SQLite config with PostgreSQL
sqlite_pattern = r"# Database - SQLite.*?\n.*?\}\n.*?\}"
postgres_config = """# Database - PostgreSQL (production-ready)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'hms_db'),
        'USER': os.getenv('DB_USER', 'hms_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'StrongPassword123!'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5434'),
    }
}"""

content = re.sub(sqlite_pattern, postgres_config, content, flags=re.DOTALL)

# Write back
with open('hms_project/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Settings switched back to PostgreSQL")
