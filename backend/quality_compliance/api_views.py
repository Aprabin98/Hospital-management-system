from datetime import date, datetime, timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit.utils import log_audit_event
from quality_compliance.api_serializers import BackupRestoreDrillSerializer
from quality_compliance.api_serializers import IncidentReportSerializer
from quality_compliance.api_serializers import RetentionPolicySerializer
from quality_compliance.api_serializers import SlaBreachSerializer
from quality_compliance.models import BackupRestoreDrill
from quality_compliance.models import IncidentReport
from quality_compliance.models import RetentionPolicy
from quality_compliance.models import SlaBreach

ALLOWED_ROLES = {'ADMIN', 'QUALITY_COMPLIANCE_OFFICER'}


def _has_access(user):
    return bool(user and user.is_authenticated and user.role in ALLOWED_ROLES)


def _deny():
    return Response({'detail': 'Access denied. Compliance role required.'}, status=status.HTTP_403_FORBIDDEN)


def _parse_date(raw_value):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None


def _parse_datetime(raw_value):
    if not raw_value:
        return None
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _full_name(user):
    if not user:
        return ''
    name = f'{getattr(user, "first_name", "")} {getattr(user, "last_name", "")}'.strip()
    return name or getattr(user, 'email', '') or ''


def _paginate(queryset, page, page_size):
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    return total, queryset[start:end]


def _incident_payload(incident):
    return {
        'id': incident.id,
        'title': incident.title,
        'incident_type': incident.incident_type,
        'severity': incident.severity,
        'status': incident.status,
        'description': incident.description,
        'root_cause': incident.root_cause,
        'corrective_action': incident.corrective_action,
        'preventive_action': incident.preventive_action,
        'closure_notes': incident.closure_notes,
        'reported_by': incident.reported_by_id,
        'reported_by_name': _full_name(incident.reported_by),
        'assigned_to': incident.assigned_to_id,
        'assigned_to_name': _full_name(incident.assigned_to),
        'reported_at': incident.reported_at,
        'triaged_at': incident.triaged_at,
        'resolved_at': incident.resolved_at,
        'due_date': incident.due_date,
    }


def _breach_payload(breach):
    return {
        'id': breach.id,
        'process_name': breach.process_name,
        'reference_number': breach.reference_number,
        'category': breach.category,
        'severity': breach.severity,
        'status': breach.status,
        'expected_at': breach.expected_at,
        'breached_at': breach.breached_at,
        'owner_role': breach.owner_role,
        'description': breach.description,
        'resolution_summary': breach.resolution_summary,
        'escalated_to': breach.escalated_to_id,
        'escalated_to_name': _full_name(breach.escalated_to),
        'acknowledged_by': breach.acknowledged_by_id,
        'acknowledged_by_name': _full_name(breach.acknowledged_by),
        'escalated_at': breach.escalated_at,
        'resolved_at': breach.resolved_at,
        'is_overdue': breach.expected_at < timezone.now() and breach.status != 'RESOLVED',
    }


def _drill_payload(drill):
    return {
        'id': drill.id,
        'drill_type': drill.drill_type,
        'environment': drill.environment,
        'runbook_version': drill.runbook_version,
        'success': drill.success,
        'duration_minutes': drill.duration_minutes,
        'rpo_minutes': drill.rpo_minutes,
        'rto_minutes': drill.rto_minutes,
        'notes': drill.notes,
        'evidence_url': drill.evidence_url,
        'executor': drill.executor_id,
        'executor_name': _full_name(drill.executor),
        'verified_by': drill.verified_by_id,
        'verified_by_name': _full_name(drill.verified_by),
        'verified_at': drill.verified_at,
        'executed_at': drill.executed_at,
        'next_due_at': drill.next_due_at,
    }


def _policy_payload(policy):
    return {
        'id': policy.id,
        'module_name': policy.module_name,
        'policy_name': policy.policy_name,
        'retention_days': policy.retention_days,
        'archive_after_days': policy.archive_after_days,
        'active': policy.active,
        'owner_role': policy.owner_role,
        'summary': policy.summary,
        'last_executed_at': policy.last_executed_at,
        'next_review_at': policy.next_review_at,
        'updated_by': policy.updated_by_id,
        'updated_by_name': _full_name(policy.updated_by),
        'updated_at': policy.updated_at,
    }


def _compliance_score(open_incidents, overdue_incidents, open_breaches, failed_drills, due_reviews):
    penalty = min(open_incidents * 4, 30)
    penalty += min(overdue_incidents * 8, 25)
    penalty += min(open_breaches * 3, 15)
    penalty += min(failed_drills * 10, 20)
    penalty += min(due_reviews * 2, 10)
    return max(0, 100 - penalty)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def compliance_dashboard_api(request):
    if not _has_access(request.user):
        return _deny()

    now = timezone.now()
    today = timezone.localdate()

    incidents = IncidentReport.objects.all()
    sla_breaches = SlaBreach.objects.all()
    drills = BackupRestoreDrill.objects.all()
    policies = RetentionPolicy.objects.all()

    open_incidents = incidents.filter(status__in=['OPEN', 'TRIAGED', 'INVESTIGATING']).count()
    overdue_incidents = incidents.filter(status__in=['OPEN', 'TRIAGED', 'INVESTIGATING'], due_date__lt=today).count()
    open_breaches = sla_breaches.exclude(status__in=['RESOLVED', 'WAIVED']).count()
    failed_drills = drills.filter(success=False).count()
    due_reviews = policies.filter(active=True).filter(next_review_at__lte=today).count()

    last_successful_drill = drills.filter(success=True).order_by('-executed_at').first()
    latest_drill = drills.order_by('-executed_at').first()
    if latest_drill:
        next_due_drill_date = latest_drill.next_due_at
    else:
        next_due_drill_date = None

    return Response(
        {
            'incident_summary': {
                'total_incidents': incidents.count(),
                'open_incidents': open_incidents,
                'overdue_incidents': overdue_incidents,
                'by_status': list(incidents.values('status').annotate(count=Count('id')).order_by('status')),
                'by_severity': list(incidents.values('severity').annotate(count=Count('id')).order_by('severity')),
                'by_type': list(incidents.values('incident_type').annotate(count=Count('id')).order_by('incident_type')),
            },
            'sla_summary': {
                'total_breaches': sla_breaches.count(),
                'open_breaches': open_breaches,
                'escalated_breaches': sla_breaches.filter(status='ESCALATED').count(),
                'overdue_breaches': sla_breaches.filter(expected_at__lt=now).exclude(status__in=['RESOLVED', 'WAIVED']).count(),
                'by_status': list(sla_breaches.values('status').annotate(count=Count('id')).order_by('status')),
            },
            'drill_summary': {
                'total_drills': drills.count(),
                'success_rate': round((drills.filter(success=True).count() / drills.count() * 100), 1) if drills.exists() else 0,
                'failed_drills': failed_drills,
                'last_successful_drill_at': last_successful_drill.executed_at if last_successful_drill else None,
                'next_due_drill_at': next_due_drill_date,
            },
            'retention_summary': {
                'active_policies': policies.filter(active=True).count(),
                'policies_due_review': due_reviews,
                'by_module': list(policies.values('module_name').annotate(count=Count('id')).order_by('module_name')),
            },
            'compliance_score': _compliance_score(open_incidents, overdue_incidents, open_breaches, failed_drills, due_reviews),
            'recent_incidents': [_incident_payload(incident) for incident in incidents.order_by('-reported_at')[:5]],
            'recent_breaches': [_breach_payload(breach) for breach in sla_breaches.order_by('-breached_at')[:5]],
            'recent_drills': [_drill_payload(drill) for drill in drills.order_by('-executed_at')[:5]],
            'recent_policies': [_policy_payload(policy) for policy in policies.order_by('module_name', 'policy_name')[:5]],
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def compliance_evidence_export_api(request):
    if not _has_access(request.user):
        return _deny()

    incidents = IncidentReport.objects.order_by('-reported_at')[:20]
    breaches = SlaBreach.objects.order_by('-breached_at')[:20]
    drills = BackupRestoreDrill.objects.order_by('-executed_at')[:20]
    policies = RetentionPolicy.objects.order_by('module_name', 'policy_name')[:20]

    return Response(
        {
            'generated_at': timezone.now(),
            'summary': {
                'incident_count': IncidentReport.objects.count(),
                'sla_breach_count': SlaBreach.objects.count(),
                'backup_drill_count': BackupRestoreDrill.objects.count(),
                'retention_policy_count': RetentionPolicy.objects.count(),
            },
            'incidents': [_incident_payload(incident) for incident in incidents],
            'sla_breaches': [_breach_payload(breach) for breach in breaches],
            'backup_drills': [_drill_payload(drill) for drill in drills],
            'retention_policies': [_policy_payload(policy) for policy in policies],
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def incidents_api(request):
    if not _has_access(request.user):
        return _deny()

    if request.method == 'GET':
        incidents = IncidentReport.objects.all()
        status_filter = (request.query_params.get('status') or '').strip().upper()
        severity_filter = (request.query_params.get('severity') or '').strip().upper()
        type_filter = (request.query_params.get('incident_type') or '').strip().upper()
        query = (request.query_params.get('q') or '').strip()
        date_from = _parse_date(request.query_params.get('date_from'))
        date_to = _parse_date(request.query_params.get('date_to'))

        if status_filter:
            incidents = incidents.filter(status=status_filter)
        if severity_filter:
            incidents = incidents.filter(severity=severity_filter)
        if type_filter:
            incidents = incidents.filter(incident_type=type_filter)
        if date_from:
            incidents = incidents.filter(reported_at__date__gte=date_from)
        if date_to:
            incidents = incidents.filter(reported_at__date__lte=date_to)
        if query:
            incidents = incidents.filter(Q(title__icontains=query) | Q(description__icontains=query))

        page = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 20) or 20)
        total, items = _paginate(incidents.order_by('-reported_at'), page, page_size)
        return Response({'count': total, 'results': [_incident_payload(item) for item in items]}, status=status.HTTP_200_OK)

    serializer = IncidentReportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    incident = serializer.save(reported_by=request.user)
    log_audit_event(
        action='CREATE',
        target=incident,
        description='Compliance incident created',
        metadata={'incident_type': incident.incident_type, 'severity': incident.severity},
        actor=request.user,
        request=request,
    )
    return Response(_incident_payload(incident), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def incident_detail_api(request, incident_id):
    if not _has_access(request.user):
        return _deny()

    try:
        incident = IncidentReport.objects.get(pk=incident_id)
    except IncidentReport.DoesNotExist:
        return Response({'detail': 'Incident not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(_incident_payload(incident), status=status.HTTP_200_OK)

    serializer = IncidentReportSerializer(incident, data=request.data, partial=(request.method == 'PATCH'))
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    incident = serializer.save()
    log_audit_event(
        action='UPDATE',
        target=incident,
        description='Compliance incident updated',
        metadata={'status': incident.status},
        actor=request.user,
        request=request,
    )
    return Response(_incident_payload(incident), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def incident_triage_api(request, incident_id):
    if not _has_access(request.user):
        return _deny()

    try:
        incident = IncidentReport.objects.get(pk=incident_id)
    except IncidentReport.DoesNotExist:
        return Response({'detail': 'Incident not found.'}, status=status.HTTP_404_NOT_FOUND)

    incident.status = 'TRIAGED'
    incident.triaged_at = timezone.now()
    assigned_to_id = request.data.get('assigned_to') or request.data.get('assigned_to_id')
    if assigned_to_id:
        incident.assigned_to_id = assigned_to_id
    if request.data.get('status') == 'INVESTIGATING':
        incident.status = 'INVESTIGATING'
    incident.save()

    log_audit_event(
        action='UPDATE',
        target=incident,
        description='Compliance incident triaged',
        metadata={'assigned_to': incident.assigned_to_id, 'status': incident.status},
        actor=request.user,
        request=request,
    )
    return Response(_incident_payload(incident), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def incident_resolve_api(request, incident_id):
    if not _has_access(request.user):
        return _deny()

    try:
        incident = IncidentReport.objects.get(pk=incident_id)
    except IncidentReport.DoesNotExist:
        return Response({'detail': 'Incident not found.'}, status=status.HTTP_404_NOT_FOUND)

    incident.status = 'CLOSED'
    incident.root_cause = request.data.get('root_cause', incident.root_cause)
    incident.corrective_action = request.data.get('corrective_action', incident.corrective_action)
    incident.preventive_action = request.data.get('preventive_action', incident.preventive_action)
    incident.closure_notes = request.data.get('closure_notes', incident.closure_notes)
    incident.resolved_at = timezone.now()
    if request.data.get('status') == 'RCA_COMPLETE':
        incident.status = 'RCA_COMPLETE'
    incident.save()

    log_audit_event(
        action='UPDATE',
        target=incident,
        description='Compliance incident resolved',
        metadata={'status': incident.status},
        actor=request.user,
        request=request,
    )
    return Response(_incident_payload(incident), status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sla_breaches_api(request):
    if not _has_access(request.user):
        return _deny()

    if request.method == 'GET':
        breaches = SlaBreach.objects.all()
        status_filter = (request.query_params.get('status') or '').strip().upper()
        category_filter = (request.query_params.get('category') or '').strip().upper()
        severity_filter = (request.query_params.get('severity') or '').strip().upper()
        if status_filter:
            breaches = breaches.filter(status=status_filter)
        if category_filter:
            breaches = breaches.filter(category=category_filter)
        if severity_filter:
            breaches = breaches.filter(severity=severity_filter)

        page = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 20) or 20)
        total, items = _paginate(breaches.order_by('-breached_at'), page, page_size)
        return Response({'count': total, 'results': [_breach_payload(item) for item in items]}, status=status.HTTP_200_OK)

    serializer = SlaBreachSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    breach = serializer.save()
    log_audit_event(
        action='CREATE',
        target=breach,
        description='SLA breach created',
        metadata={'category': breach.category, 'severity': breach.severity},
        actor=request.user,
        request=request,
    )
    return Response(_breach_payload(breach), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def sla_breach_detail_api(request, breach_id):
    if not _has_access(request.user):
        return _deny()

    try:
        breach = SlaBreach.objects.get(pk=breach_id)
    except SlaBreach.DoesNotExist:
        return Response({'detail': 'SLA breach not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(_breach_payload(breach), status=status.HTTP_200_OK)

    serializer = SlaBreachSerializer(breach, data=request.data, partial=(request.method == 'PATCH'))
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    breach = serializer.save()
    return Response(_breach_payload(breach), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sla_breach_escalate_api(request, breach_id):
    if not _has_access(request.user):
        return _deny()

    try:
        breach = SlaBreach.objects.get(pk=breach_id)
    except SlaBreach.DoesNotExist:
        return Response({'detail': 'SLA breach not found.'}, status=status.HTTP_404_NOT_FOUND)

    breach.status = 'ESCALATED'
    breach.escalated_at = timezone.now()
    escalated_to_id = request.data.get('escalated_to') or request.data.get('escalated_to_id')
    if escalated_to_id:
        breach.escalated_to_id = escalated_to_id
    breach.save()

    log_audit_event(
        action='UPDATE',
        target=breach,
        description='SLA breach escalated',
        metadata={'escalated_to': breach.escalated_to_id},
        actor=request.user,
        request=request,
    )
    return Response(_breach_payload(breach), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sla_breach_resolve_api(request, breach_id):
    if not _has_access(request.user):
        return _deny()

    try:
        breach = SlaBreach.objects.get(pk=breach_id)
    except SlaBreach.DoesNotExist:
        return Response({'detail': 'SLA breach not found.'}, status=status.HTTP_404_NOT_FOUND)

    breach.status = 'RESOLVED'
    breach.resolution_summary = request.data.get('resolution_summary', breach.resolution_summary)
    breach.acknowledged_by = request.user
    breach.resolved_at = timezone.now()
    breach.save()

    log_audit_event(
        action='UPDATE',
        target=breach,
        description='SLA breach resolved',
        metadata={'status': breach.status},
        actor=request.user,
        request=request,
    )
    return Response(_breach_payload(breach), status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def backup_drills_api(request):
    if not _has_access(request.user):
        return _deny()

    if request.method == 'GET':
        drills = BackupRestoreDrill.objects.all()
        drill_type = (request.query_params.get('drill_type') or '').strip().upper()
        if drill_type:
            drills = drills.filter(drill_type=drill_type)

        page = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 20) or 20)
        total, items = _paginate(drills.order_by('-executed_at'), page, page_size)
        return Response({'count': total, 'results': [_drill_payload(item) for item in items]}, status=status.HTTP_200_OK)

    serializer = BackupRestoreDrillSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    drill = serializer.save(executor=request.user)
    log_audit_event(
        action='CREATE',
        target=drill,
        description='Backup/restore drill recorded',
        metadata={'drill_type': drill.drill_type, 'success': drill.success},
        actor=request.user,
        request=request,
    )
    return Response(_drill_payload(drill), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def backup_drill_detail_api(request, drill_id):
    if not _has_access(request.user):
        return _deny()

    try:
        drill = BackupRestoreDrill.objects.get(pk=drill_id)
    except BackupRestoreDrill.DoesNotExist:
        return Response({'detail': 'Drill not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(_drill_payload(drill), status=status.HTTP_200_OK)

    serializer = BackupRestoreDrillSerializer(drill, data=request.data, partial=(request.method == 'PATCH'))
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    drill = serializer.save()
    return Response(_drill_payload(drill), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def backup_drill_verify_api(request, drill_id):
    if not _has_access(request.user):
        return _deny()

    try:
        drill = BackupRestoreDrill.objects.get(pk=drill_id)
    except BackupRestoreDrill.DoesNotExist:
        return Response({'detail': 'Drill not found.'}, status=status.HTTP_404_NOT_FOUND)

    drill.verified_by = request.user
    drill.verified_at = timezone.now()
    if 'success' in request.data:
        drill.success = bool(request.data.get('success'))
    if request.data.get('notes'):
        drill.notes = request.data.get('notes')
    drill.save()

    log_audit_event(
        action='UPDATE',
        target=drill,
        description='Backup/restore drill verified',
        metadata={'success': drill.success},
        actor=request.user,
        request=request,
    )
    return Response(_drill_payload(drill), status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def retention_policies_api(request):
    if not _has_access(request.user):
        return _deny()

    if request.method == 'GET':
        policies = RetentionPolicy.objects.all()
        active_param = request.query_params.get('active')
        if active_param in {'1', 'true', 'yes'}:
            policies = policies.filter(active=True)
        if active_param in {'0', 'false', 'no'}:
            policies = policies.filter(active=False)

        page = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 20) or 20)
        total, items = _paginate(policies.order_by('module_name', 'policy_name'), page, page_size)
        return Response({'count': total, 'results': [_policy_payload(item) for item in items]}, status=status.HTTP_200_OK)

    serializer = RetentionPolicySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    policy = serializer.save(updated_by=request.user)
    log_audit_event(
        action='CREATE',
        target=policy,
        description='Retention policy created',
        metadata={'module_name': policy.module_name, 'policy_name': policy.policy_name},
        actor=request.user,
        request=request,
    )
    return Response(_policy_payload(policy), status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def retention_policy_detail_api(request, policy_id):
    if not _has_access(request.user):
        return _deny()

    try:
        policy = RetentionPolicy.objects.get(pk=policy_id)
    except RetentionPolicy.DoesNotExist:
        return Response({'detail': 'Retention policy not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(_policy_payload(policy), status=status.HTTP_200_OK)

    serializer = RetentionPolicySerializer(policy, data=request.data, partial=(request.method == 'PATCH'))
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    policy = serializer.save(updated_by=request.user)
    return Response(_policy_payload(policy), status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retention_policy_execute_api(request, policy_id):
    if not _has_access(request.user):
        return _deny()

    try:
        policy = RetentionPolicy.objects.get(pk=policy_id)
    except RetentionPolicy.DoesNotExist:
        return Response({'detail': 'Retention policy not found.'}, status=status.HTTP_404_NOT_FOUND)

    policy.last_executed_at = timezone.now()
    review_offset = max(30, min(policy.retention_days, 365))
    policy.next_review_at = (timezone.localdate() + timedelta(days=review_offset))
    policy.updated_by = request.user
    policy.save()

    log_audit_event(
        action='UPDATE',
        target=policy,
        description='Retention policy executed',
        metadata={'module_name': policy.module_name, 'policy_name': policy.policy_name},
        actor=request.user,
        request=request,
    )
    return Response(_policy_payload(policy), status=status.HTTP_200_OK)