from threading import local


_request_local = local()


def set_current_request(request):
    _request_local.request = request


def get_current_request():
    return getattr(_request_local, 'request', None)


def clear_current_request():
    if hasattr(_request_local, 'request'):
        del _request_local.request


class AuditRequestMiddleware:
    """Store current request for signal-based audit logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        try:
            response = self.get_response(request)
            return response
        finally:
            clear_current_request()
