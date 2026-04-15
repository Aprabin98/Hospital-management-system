from audit.middleware import get_current_request
from audit.models import AuditLog


def get_client_ip(request):
    if not request:
        return None

    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _extract_target_fields(target):
    if not target:
        return '', '', ''

    if isinstance(target, dict):
        return (
            str(target.get('model_name', '')),
            str(target.get('object_id', '')),
            str(target.get('object_repr', '')),
        )

    meta = getattr(target, '_meta', None)
    model_name = f"{meta.app_label}.{meta.model_name}" if meta else target.__class__.__name__
    object_id = str(getattr(target, 'pk', '') or '')
    object_repr = str(target)
    return model_name, object_id, object_repr


def log_audit_event(action, target=None, description='', metadata=None, actor=None, request=None):
    request = request or get_current_request()

    if actor is None and request and getattr(request, 'user', None) and request.user.is_authenticated:
        actor = request.user

    model_name, object_id, object_repr = _extract_target_fields(target)

    actor_email = ''
    actor_role = ''
    if actor is not None:
        actor_email = getattr(actor, 'email', '') or ''
        actor_role = getattr(actor, 'role', '') or ''

    request_meta = getattr(request, 'META', {}) if request else {}
    request_path = (getattr(request, 'path', '') if request else '') or ''
    request_method = (getattr(request, 'method', '') if request else '') or ''

    AuditLog.objects.create(
        actor=actor,
        actor_email=actor_email,
        actor_role=actor_role,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr[:255],
        description=description,
        metadata=metadata or {},
        ip_address=get_client_ip(request),
        user_agent=(request_meta.get('HTTP_USER_AGENT', '') or '')[:1000],
        path=request_path[:255],
        method=request_method[:10],
    )
