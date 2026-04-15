"""API views for audit logs."""
from datetime import date

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit.models import AuditLog


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_logs_list_api(request):
    """
    GET: List audit logs for admin users.
    Supports query filters:
    - action
    - q (search in description/actor/model/object/path)
    - date_from (YYYY-MM-DD)
    - date_to (YYYY-MM-DD)
    - page, page_size
    """
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied. Admin only.'}, status=status.HTTP_403_FORBIDDEN)

    action = (request.query_params.get('action') or '').strip().upper()
    query = (request.query_params.get('q') or '').strip()
    date_from_raw = (request.query_params.get('date_from') or '').strip()
    date_to_raw = (request.query_params.get('date_to') or '').strip()

    date_from = None
    date_to = None

    if date_from_raw:
        try:
            date_from = date.fromisoformat(date_from_raw)
        except ValueError:
            return Response({'detail': 'Invalid date_from format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    if date_to_raw:
        try:
            date_to = date.fromisoformat(date_to_raw)
        except ValueError:
            return Response({'detail': 'Invalid date_to format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    if date_from and date_to and date_from > date_to:
        return Response({'detail': 'date_from cannot be greater than date_to.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 30))
    except (TypeError, ValueError):
        page = 1
        page_size = 30

    page = max(1, page)
    page_size = max(1, min(100, page_size))

    logs = AuditLog.objects.all().order_by('-created_at')

    if action:
        logs = logs.filter(action=action)

    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)

    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)

    if query:
        from django.db.models import Q
        logs = logs.filter(
            Q(description__icontains=query)
            | Q(actor_email__icontains=query)
            | Q(model_name__icontains=query)
            | Q(object_repr__icontains=query)
            | Q(path__icontains=query)
        )

    total_count = logs.count()
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    results = []
    for log in logs[start_idx:end_idx]:
        results.append({
            'id': log.id,
            'created_at': log.created_at,
            'action': log.action,
            'actor_email': log.actor_email,
            'actor_role': log.actor_role,
            'model_name': log.model_name,
            'object_id': log.object_id,
            'object_repr': log.object_repr,
            'description': log.description,
            'ip_address': log.ip_address,
            'path': log.path,
            'method': log.method,
            'metadata': log.metadata,
        })

    return Response(
        {
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'results': results,
        },
        status=status.HTTP_200_OK,
    )
