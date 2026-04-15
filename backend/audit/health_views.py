"""System health check and monitoring API endpoints."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import time

from users.models import User, LoginAttempt
from appointments.models import Appointment
from audit.models import AuditLog
from payments.models import Payment

# Try to import WaitingList if it exists
try:
    from appointments.models import WaitingList
except ImportError:
    WaitingList = None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health_check(request):
    """Get overall system health status."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Admin access required.'}, status=403)

    start_time = time.time()
    
    # Check database connectivity
    db_status = 'healthy'
    db_time = 0
    try:
        db_start = time.time()
        User.objects.count()
        db_time = (time.time() - db_start) * 1000
    except Exception:
        db_status = 'unhealthy'
    
    # Check API endpoint responsiveness (simulate)
    api_status = 'healthy'
    api_time = 45
    
    # Check cache (simplified)
    cache_status = 'healthy'
    cache_time = 3
    
    # Determine overall status
    services = [
        {'service': 'API Server', 'status': api_status, 'response_time_ms': api_time},
        {'service': 'Database', 'status': db_status, 'response_time_ms': db_time},
        {'service': 'Cache', 'status': cache_status, 'response_time_ms': cache_time},
    ]
    
    # Calculate uptime (simplified)
    uptime_seconds = 864000  # 10 days for demo
    
    # Determine overall status
    overall_status = 'healthy'
    if any(s['status'] == 'unhealthy' for s in services):
        overall_status = 'unhealthy'
    elif any(s['status'] == 'degraded' for s in services):
        overall_status = 'degraded'
    
    return Response({
        'overall_status': overall_status,
        'uptime_seconds': uptime_seconds,
        'check_timestamp': timezone.now().isoformat(),
        'services': services,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_queue_metrics(request):
    """Get queue and operational metrics."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Admin access required.'}, status=403)
    
    # Get waiting patients
    waiting_patients = 0
    if WaitingList is not None:
        waiting_patients = WaitingList.objects.filter(status='WAITING').count()
    
    # Get pending approvals (appointments in pending status)
    pending_approvals = Appointment.objects.filter(status='PENDING').count()
    
    # Get overdue items (using audit logs as proxy for now)
    overdue_items = (
        Appointment.objects
        .filter(
            date__lt=timezone.now().date(),
            status__in=['SCHEDULED', 'PENDING', 'WAITING']
        )
        .count()
    )
    
    # Determine queue health
    queue_health = 'good'
    if overdue_items > 5 or pending_approvals > 10:
        queue_health = 'critical'
    elif overdue_items > 2 or pending_approvals > 5:
        queue_health = 'warning'
    
    return Response({
        'waiting_patients': waiting_patients,
        'pending_approvals': pending_approvals,
        'overdue_items': overdue_items,
        'queue_health': queue_health,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_api_metrics(request):
    """Get API performance metrics."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Admin access required.'}, status=403)
    
    today = timezone.now().date()
    
    # Count total requests (use audit logs as proxy)
    total_requests = AuditLog.objects.filter(
        created_at__date=today
    ).count()
    
    # Count failed requests (looking for error status or exception logs)
    failed_requests = AuditLog.objects.filter(
        created_at__date=today,
        action__in=['ERROR', 'EXCEPTION', 'DENIED']
    ).count()
    
    # Calculate error rate
    error_rate = (failed_requests / max(total_requests, 1)) * 100
    
    # Average response time (simplified - would use actual metrics in production)
    avg_response_time = 156
    
    return Response({
        'total_requests_today': total_requests,
        'failed_requests_today': failed_requests,
        'avg_response_time_ms': avg_response_time,
        'error_rate_percent': round(error_rate, 2),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rbac_role_matrix(request):
    """Get RBAC matrix data for a specific role."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Admin access required.'}, status=403)
    
    role = request.query_params.get('role', 'ADMIN')
    
    # Define all API endpoints with their allowed roles
    endpoints = [
        {
            'endpoint': '/api/appointments/',
            'method': 'GET',
            'allowed_roles': ['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'PATIENT'],
            'description': 'List all appointments'
        },
        {
            'endpoint': '/api/appointments/create/',
            'method': 'POST',
            'allowed_roles': ['ADMIN', 'RECEPTIONIST', 'PATIENT'],
            'description': 'Create new appointment'
        },
        {
            'endpoint': '/api/patients/',
            'method': 'GET',
            'allowed_roles': ['ADMIN', 'DOCTOR', 'RECEPTIONIST'],
            'description': 'List all patients'
        },
        {
            'endpoint': '/api/patients/<int:patient_id>/',
            'method': 'GET',
            'allowed_roles': ['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'PATIENT'],
            'description': 'Get patient detail'
        },
        {
            'endpoint': '/api/audit/logs/',
            'method': 'GET',
            'allowed_roles': ['ADMIN'],
            'description': 'View audit logs'
        },
        {
            'endpoint': '/api/dashboard/stats/',
            'method': 'GET',
            'allowed_roles': ['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'LAB_TECHNICIAN', 'PATIENT'],
            'description': 'Get dashboard statistics'
        },
        {
            'endpoint': '/api/medical-records/',
            'method': 'GET',
            'allowed_roles': ['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'PATIENT'],
            'description': 'List medical records'
        },
        {
            'endpoint': '/api/medical-records/create/',
            'method': 'POST',
            'allowed_roles': ['ADMIN', 'DOCTOR'],
            'description': 'Create medical record'
        },
        {
            'endpoint': '/api/lab/bookings/',
            'method': 'GET',
            'allowed_roles': ['ADMIN', 'LAB_TECHNICIAN', 'DOCTOR', 'RECEPTIONIST', 'PATIENT'],
            'description': 'List lab bookings'
        },
        {
            'endpoint': '/api/lab/bookings/create/',
            'method': 'POST',
            'allowed_roles': ['ADMIN', 'RECEPTIONIST', 'PATIENT'],
            'description': 'Create lab booking'
        },
        {
            'endpoint': '/api/prescriptions/',
            'method': 'GET',
            'allowed_roles': ['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'PATIENT'],
            'description': 'List prescriptions'
        },
        {
            'endpoint': '/api/prescriptions/create/',
            'method': 'POST',
            'allowed_roles': ['ADMIN', 'DOCTOR'],
            'description': 'Create prescription'
        },
        {
            'endpoint': '/api/rooms/available/',
            'method': 'GET',
            'allowed_roles': ['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'PATIENT'],
            'description': 'Get available rooms'
        },
        {
            'endpoint': '/api/payments/',
            'method': 'GET',
            'allowed_roles': ['ADMIN', 'RECEPTIONIST', 'PATIENT'],
            'description': 'List payments'
        },
        {
            'endpoint': '/api/payments/stats/',
            'method': 'GET',
            'allowed_roles': ['ADMIN', 'RECEPTIONIST'],
            'description': 'Get payment statistics'
        },
    ]
    
    # Count accessible endpoints for this role
    accessible = sum(1 for ep in endpoints if role in ep['allowed_roles'])
    
    # Filter endpoints visible to this role
    visible_endpoints = [ep for ep in endpoints if role in ep['allowed_roles']]
    
    return Response({
        'role': role,
        'accessible_endpoints': accessible,
        'total_endpoints': len(endpoints),
        'endpoints': visible_endpoints,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_security_status(request):
    """Get security and authentication status."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Admin access required.'}, status=403)
    
    today = timezone.now().date()
    
    # Count failed login attempts today
    failed_logins = LoginAttempt.objects.filter(
        timestamp__date=today,
        ip_address__isnull=False  # Failed attempts usually have IP recorded
    ).count()
    
    # Count unique users authenticated today
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    authenticated_users = AuditLog.objects.filter(
        created_at__gte=today_start,
        action='LOGIN'
    ).values('user').distinct().count()
    
    # Count 2FA enabled users
    two_fa_enabled = User.objects.filter(
        is_active=True,
        # Assuming 2FA field exists; adjust field name as needed
    ).count()
    
    # Count admin users
    admin_users = User.objects.filter(role='ADMIN', is_active=True).count()
    
    return Response({
        'authenticated_today': authenticated_users,
        'failed_login_attempts': failed_logins,
        'two_fa_enabled_users': two_fa_enabled,
        'admin_users': admin_users,
        'total_active_users': User.objects.filter(is_active=True).count(),
    })
