#!/usr/bin/env python
"""
Compatibility wrapper for running Django commands from repository root.

Canonical Django entrypoint: backend/manage.py
"""

from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hms_project.settings")

from django.core.management import execute_from_command_line  # noqa: E402


if __name__ == "__main__":
    execute_from_command_line(sys.argv)
