from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


class SecurityHeadersMiddleware:
    """Adds basic security headers to all responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'same-origin')
        response.setdefault('X-Frame-Options', 'DENY')
        return response


class RequestRateLimitMiddleware:
    """Apply endpoint-level rate limits for sensitive auth actions."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, 'RATE_LIMIT_ENABLED', True):
            blocked_response = self._check_limit(request)
            if blocked_response is not None:
                return blocked_response
        return self.get_response(request)

    def _check_limit(self, request):
        rules = getattr(settings, 'RATE_LIMIT_RULES', {})
        path = request.path
        rule = rules.get(path)
        if not rule:
            return None

        if request.method != rule.get('method', 'POST'):
            return None

        limit = int(rule.get('limit', 10))
        window = int(rule.get('window_seconds', 300))

        ip_address = self._client_ip(request)
        identifier = self._identifier(request)

        cache_key = f"ratelimit:{path}:{ip_address}:{identifier}"
        current = cache.get(cache_key, 0)
        if current >= limit:
            self._log_limit_event(request, path, ip_address, identifier, limit, window)
            return HttpResponse(
                'Too many requests. Please wait and try again.',
                status=429,
            )

        if current == 0:
            cache.set(cache_key, 1, timeout=window)
        else:
            cache.incr(cache_key)

        return None

    def _client_ip(self, request):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

    def _identifier(self, request):
        value = ''
        if request.method == 'POST':
            value = request.POST.get('email', '')
            if not value:
                value = request.POST.get('username', '')
        return (value or '').strip().lower() or 'anonymous'

    def _log_limit_event(self, request, path, ip_address, identifier, limit, window):
        try:
            from audit.utils import log_audit_event

            log_audit_event(
                action='SECURITY',
                request=request,
                description='Rate limit exceeded on sensitive endpoint.',
                metadata={
                    'path': path,
                    'ip': ip_address,
                    'identifier': identifier,
                    'limit': limit,
                    'window_seconds': window,
                },
            )
        except Exception:
            # Never break request flow due to audit side effects.
            pass
