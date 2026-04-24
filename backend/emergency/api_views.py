from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .api_serializers import (
    EmergencyClinicalNoteSerializer,
    EmergencyEncounterSerializer,
    EmergencyTriageSerializer,
)
from .models import EmergencyClinicalNote, EmergencyEncounter


_ALLOWED_EMERGENCY_ROLES = {
    'ADMIN',
    'DOCTOR',
    'NURSE',
    'RECEPTIONIST',
}


def _can_access_emergency(user):
    return user.is_authenticated and user.role in _ALLOWED_EMERGENCY_ROLES


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def emergency_encounter_list_create_api(request):
    if not _can_access_emergency(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        queryset = EmergencyEncounter.objects.select_related(
            'patient__user',
            'assigned_doctor__user',
        ).all()
        serializer = EmergencyEncounterSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = EmergencyEncounterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(created_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def emergency_encounter_detail_api(request, encounter_id):
    if not _can_access_emergency(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        encounter = EmergencyEncounter.objects.get(pk=encounter_id)
    except EmergencyEncounter.DoesNotExist:
        return Response({'detail': 'Encounter not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EmergencyEncounterSerializer(encounter)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = EmergencyEncounterSerializer(encounter, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    instance = serializer.save()
    if instance.status in {'ADMITTED', 'TRANSFERRED', 'DISCHARGED', 'DECEASED'} and not instance.closed_at:
        instance.closed_at = timezone.now()
        instance.save(update_fields=['closed_at'])
    return Response(EmergencyEncounterSerializer(instance).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def emergency_triage_queue_api(request):
    if not _can_access_emergency(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    queue = EmergencyEncounter.objects.select_related(
        'patient__user',
        'assigned_doctor__user',
    ).filter(status__in=['REGISTERED', 'TRIAGED', 'IN_TREATMENT']).order_by('severity_priority', 'arrived_at')
    serializer = EmergencyEncounterSerializer(queue, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def emergency_triage_records_api(request, encounter_id):
    if not _can_access_emergency(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        encounter = EmergencyEncounter.objects.get(pk=encounter_id)
    except EmergencyEncounter.DoesNotExist:
        return Response({'detail': 'Encounter not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EmergencyTriageSerializer(encounter.triage_records.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = EmergencyTriageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(encounter=encounter, triaged_by=request.user)

    if encounter.status == 'REGISTERED':
        encounter.status = 'TRIAGED'
    if not encounter.triaged_at:
        encounter.triaged_at = timezone.now()
    encounter.save(update_fields=['status', 'triaged_at'])

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def emergency_notes_api(request, encounter_id):
    if not _can_access_emergency(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        encounter = EmergencyEncounter.objects.get(pk=encounter_id)
    except EmergencyEncounter.DoesNotExist:
        return Response({'detail': 'Encounter not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EmergencyClinicalNoteSerializer(encounter.clinical_notes.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = EmergencyClinicalNoteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(encounter=encounter, authored_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
