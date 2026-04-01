from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import LoginAttempt


def _max_failed_attempts():
    return int(getattr(settings, 'LOGIN_MAX_FAILED_ATTEMPTS', 5))


def _lock_minutes():
    return int(getattr(settings, 'LOGIN_LOCK_MINUTES', 30))


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
def register_failed_attempt(identifier, ip_address='', request=None):
    if not identifier:
        return None

    attempt, _ = LoginAttempt.objects.get_or_create(identifier=identifier)

    now = timezone.now()
    # Reset count if last attempt is old.
    if attempt.last_attempt and now - attempt.last_attempt > timedelta(hours=2):
        attempt.failed_count = 0

    attempt.failed_count += 1
    attempt.last_attempt = now
    attempt.last_ip = ip_address

    if attempt.failed_count >= _max_failed_attempts():
        attempt.locked_until = now + timedelta(minutes=_lock_minutes())

        # Best-effort audit trail, never fail auth flow if audit write fails.
        try:
            from audit.utils import log_audit_event

            log_audit_event(
                action='SECURITY',
                request=request,
                description='Account lockout triggered after repeated failed login attempts.',
                target={
                    'model_name': 'users.loginattempt',
                    'object_id': str(attempt.pk),
                    'object_repr': identifier,
                },
                metadata={
                    'identifier': identifier,
                    'failed_count': attempt.failed_count,
                    'lock_minutes': _lock_minutes(),
                    'ip': ip_address,
                },
            )
        except Exception:
            pass

    attempt.save()
    return attempt


@transaction.atomic
def clear_attempts(identifier):
    if not identifier:
        return
    LoginAttempt.objects.filter(identifier=identifier).delete()
