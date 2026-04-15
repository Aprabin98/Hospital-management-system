"""User management API endpoints for admin."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_403_FORBIDDEN
from django.shortcuts import get_object_or_404
from django.db.models import Q

from users.models import User


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_list_api(request):
    """Get list of all users (admin only)."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Admin access required.'}, status=HTTP_403_FORBIDDEN)
    
    # Get query parameters for filtering
    role = request.query_params.get('role')
    is_active = request.query_params.get('is_active')
    search = request.query_params.get('search')
    
    # Start with all users
    queryset = User.objects.all().order_by('-date_joined')
    
    # Filter by role if provided
    if role and role != 'ALL':
        queryset = queryset.filter(role=role)
    
    # Filter by active status if provided
    if is_active is not None:
        is_active_bool = is_active.lower() in ['true', '1', 'yes']
        queryset = queryset.filter(is_active=is_active_bool)
    
    # Search by email, username, or name if provided
    if search:
        queryset = queryset.filter(
            Q(email__icontains=search) |
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 15))
    
    total_count = queryset.count()
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    users = queryset[start_idx:end_idx]
    
    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'results': [
            {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat(),
                'is_staff': user.is_staff,
            }
            for user in users
        ],
    })


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_detail_api(request, user_id):
    """Get, update, or delete a user (admin only)."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Admin access required.'}, status=HTTP_403_FORBIDDEN)
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'GET':
        return Response({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat(),
            'is_staff': user.is_staff,
        })
    
    elif request.method == 'PATCH':
        # Update user fields
        if 'role' in request.data:
            user.role = request.data['role']
        
        if 'is_active' in request.data:
            user.is_active = request.data['is_active']
        
        if 'first_name' in request.data:
            user.first_name = request.data['first_name']
        
        if 'last_name' in request.data:
            user.last_name = request.data['last_name']
        
        if 'is_staff' in request.data:
            user.is_staff = request.data['is_staff']
        
        user.save()
        
        return Response({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat(),
            'is_staff': user.is_staff,
        })
    
    elif request.method == 'DELETE':
        # Soft delete - deactivate the user instead of removing
        user.is_active = False
        user.save()
        
        return Response({'detail': 'User deactivated successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats_api(request):
    """Get user statistics (admin only)."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Admin access required.'}, status=HTTP_403_FORBIDDEN)
    
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    
    role_counts = {}
    for role_choice in User.ROLE_CHOICES:
        role_name = role_choice[0]
        role_counts[role_name] = User.objects.filter(role=role_name).count()
    
    return Response({
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'by_role': role_counts,
    })
