from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .api_serializers import OTScheduleSerializer, ProcedureNoteSerializer, PostOpNoteSerializer
from .models import OTSchedule, ProcedureNote, PostOpNote


def _has_role(user, allowed):
    return bool(user and user.is_authenticated and user.role in allowed)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ot_schedule_list_create_api(request):
    if not _has_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        queryset = OTSchedule.objects.select_related('patient__user', 'surgeon__user', 'anesthetist__user').all()
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())
        serializer = OTScheduleSerializer(queryset, many=True)
        return Response(serializer.data)

    serializer = OTScheduleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(created_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def ot_schedule_detail_api(request, schedule_id):
    if not _has_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    schedule = get_object_or_404(OTSchedule, id=schedule_id)

    if request.method == 'GET':
        return Response(OTScheduleSerializer(schedule).data)

    serializer = OTScheduleSerializer(schedule, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def ot_procedure_note_api(request, schedule_id):
    if not _has_role(request.user, ['ADMIN', 'DOCTOR']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    schedule = get_object_or_404(OTSchedule, id=schedule_id)
    note = ProcedureNote.objects.filter(schedule=schedule).first()

    if request.method == 'GET':
        if not note:
            return Response({'detail': 'Procedure note not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProcedureNoteSerializer(note).data)

    serializer = ProcedureNoteSerializer(note, data=request.data, partial=bool(note)) if note else ProcedureNoteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    saved = serializer.save(schedule=schedule, signed_by=request.user, signed_at=timezone.now())
    return Response(ProcedureNoteSerializer(saved).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ot_post_op_notes_api(request, schedule_id):
    if not _has_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    schedule = get_object_or_404(OTSchedule, id=schedule_id)

    if request.method == 'GET':
        notes = schedule.post_op_notes.select_related('created_by').all()
        return Response(PostOpNoteSerializer(notes, many=True).data)

    serializer = PostOpNoteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(schedule=schedule, created_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ot_dashboard_api(request):
    if not _has_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    today = timezone.localdate()
    return Response({
        'scheduled': OTSchedule.objects.filter(status='SCHEDULED').count(),
        'in_progress': OTSchedule.objects.filter(status='IN_PROGRESS').count(),
        'completed_today': OTSchedule.objects.filter(status='COMPLETED', scheduled_start__date=today).count(),
        'post_op_critical': PostOpNote.objects.filter(recovery_status='CRITICAL').count(),
    })
