from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.http import require_http_methods

from .models import Notification


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def notifications_list_api(request):
    """Get notifications for the authenticated user."""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
    except (ValueError, TypeError):
        page = 1
        page_size = 20

    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    unread_only = (request.GET.get('unread_only') or '').lower() in {'1', 'true', 'yes'}
    if unread_only:
        notifications = notifications.filter(is_read=False)

    total_count = notifications.count()
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    rows = notifications[start_idx:end_idx]

    results = [
        {
            'id': item.id,
            'title': item.title,
            'message': item.message,
            'notification_type': item.notification_type,
            'action_url': item.action_url,
            'is_read': item.is_read,
            'read_at': item.read_at.isoformat() if item.read_at else None,
            'metadata': item.metadata,
            'created_at': item.created_at.isoformat(),
        }
        for item in rows
    ]

    return Response(
        {
            'count': total_count,
            'next': f'/api/notifications/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/notifications/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': results,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def notifications_unread_count_api(request):
    """Get unread notification count for header badge."""
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return Response({'unread_count': unread_count}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def notification_mark_read_api(request, notification_id):
    """Mark one notification as read."""
    notification = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
    return Response({'detail': 'Notification marked as read.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def notifications_mark_all_read_api(request):
    """Mark all notifications as read for current user."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now(),
    )
    return Response({'detail': 'All notifications marked as read.'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@require_http_methods(["DELETE"])
def notification_delete_api(request, notification_id):
    """Delete one notification."""
    notification = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    notification.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
