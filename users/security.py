from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import LoginAttempt


MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 30


def is_identifier_locked(identifier):
    if not identifier:
        return False
    try:
        attempt = LoginAttempt.objects.get(identifier=identifier)
    except LoginAttempt.DoesNotExist:
        return False

    if attempt.locked_until and attempt.locked_until > timezone.now():
        return True
    return False


@transaction.atomic
def register_failed_attempt(identifier, ip_address=''):
    if not identifier:
        return

    attempt, _ = LoginAttempt.objects.get_or_create(identifier=identifier)

    now = timezone.now()
    # Reset count if last attempt is old.
    if attempt.last_attempt and now - attempt.last_attempt > timedelta(hours=2):
        attempt.failed_count = 0

    attempt.failed_count += 1
    attempt.last_attempt = now
    attempt.last_ip = ip_address

    if attempt.failed_count >= MAX_FAILED_ATTEMPTS:
        attempt.locked_until = now + timedelta(minutes=LOCK_MINUTES)

    attempt.save()


@transaction.atomic
def clear_attempts(identifier):
    if not identifier:
        return
    LoginAttempt.objects.filter(identifier=identifier).delete()
