from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.db import ProgrammingError

from audit.models import AuditLog
from audit.utils import log_audit_event


EXCLUDED_APPS = {'audit', 'admin', 'contenttypes', 'sessions'}


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    try:
        log_audit_event(
            action='LOGIN',
            actor=user,
            request=request,
            description='User logged in successfully.',
        )
    except ProgrammingError:
        # Table doesn't exist yet (during migrations)
        pass


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    if user is None:
        return
    try:
        log_audit_event(
            action='LOGOUT',
            actor=user,
            request=request,
            description='User logged out.',
        )
    except ProgrammingError:
        # Table doesn't exist yet (during migrations)
        pass


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    identifier = credentials.get('email') or credentials.get('username') or 'unknown'
    try:
        log_audit_event(
            action='LOGIN_FAILED',
            request=request,
            target={'model_name': 'auth.user', 'object_id': '', 'object_repr': identifier},
            description='Login attempt failed.',
            metadata={'identifier': identifier},
        )
    except ProgrammingError:
        # Table doesn't exist yet (during migrations)
        pass


@receiver(post_save)
def on_model_saved(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    meta = getattr(sender, '_meta', None)
    if not meta:
        return
    if meta.app_label in EXCLUDED_APPS:
        return
    if sender is AuditLog:
        return

    try:
        action = 'CREATE' if created else 'UPDATE'
        log_audit_event(
            action=action,
            target=instance,
            description=f'{action} on {meta.app_label}.{meta.model_name}',
        )
    except ProgrammingError:
        # Table doesn't exist yet (during migrations)
        pass


@receiver(post_delete)
def on_model_deleted(sender, instance, **kwargs):
    meta = getattr(sender, '_meta', None)
    if not meta:
        return
    if meta.app_label in EXCLUDED_APPS:
        return
    if sender is AuditLog:
        return

    try:
        log_audit_event(
            action='DELETE',
            target=instance,
            description=f'DELETE on {meta.app_label}.{meta.model_name}',
        )
    except ProgrammingError:
        # Table doesn't exist yet (during migrations)
        pass
