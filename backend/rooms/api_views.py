"""API views for room endpoints"""
import csv

from django.http import HttpResponse
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Count, Q
from .models import Room, RoomAssignment, AdmissionRequest, RoomBed, RoomTransfer
from .api_serializers import RoomSerializer, RoomAssignmentSerializer, AdmissionRequestSerializer


class RoomCreateSerializer(RoomSerializer):
    class Meta(RoomSerializer.Meta):
        fields = [
            'id',
            'room_number',
            'room_type',
            'floor',
            'capacity',
            'is_active',
            'notes',
            'beds',
            'created_at',
        ]

    def create(self, validated_data):
        validated_data.pop('beds', None)
        room = Room.objects.create(
            room_number=validated_data['room_number'],
            room_type=validated_data.get('room_type', 'GENERAL'),
            floor=validated_data.get('floor', ''),
            capacity=validated_data.get('capacity', 1),
            is_active=validated_data.get('is_active', True),
            notes=validated_data.get('notes', ''),
        )
        for index in range(1, room.capacity + 1):
            RoomBed.objects.create(room=room, bed_number=str(index))
        return room


class AdmissionRequestAdminSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True, allow_null=True)
    preferred_room_number = serializers.CharField(source='preferred_room.room_number', read_only=True, allow_null=True)

    class Meta:
        model = AdmissionRequest
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name', 'preferred_room', 'preferred_room_number',
            'preferred_room_type', 'reason', 'status', 'receptionist_notes', 'processed_by', 'processed_at', 'created_at'
        ]


class RoomTransferAdminSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True, allow_null=True)
    from_room_number = serializers.CharField(source='from_bed.room.room_number', read_only=True)
    from_bed_number = serializers.CharField(source='from_bed.bed_number', read_only=True)
    to_room_number = serializers.CharField(source='to_bed.room.room_number', read_only=True)
    to_bed_number = serializers.CharField(source='to_bed.bed_number', read_only=True)

    class Meta:
        model = RoomTransfer
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'from_bed', 'from_room_number', 'from_bed_number',
            'to_bed', 'to_room_number', 'to_bed_number',
            'reason', 'status', 'requested_at', 'completed_at', 'notes'
        ]



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def rooms_available_api(request):
    """Get list of available rooms"""
    try:
        rooms = (
            Room.objects
            .filter(is_active=True)
            .annotate(available_count=Count('beds', filter=Q(beds__status='AVAILABLE')))
            .filter(available_count__gt=0)
            .prefetch_related('beds')
        )
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def room_create_api(request):
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = RoomCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    room = serializer.save()
    return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def room_assignments_list_api(request):
    """Get patient's room assignments"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10
    
    # Role-scoped access to avoid broad fallback exposure.
    from users.models import PatientProfile
    try:
        patient = PatientProfile.objects.get(user=request.user)
        assignments = RoomAssignment.objects.filter(patient=patient).select_related('bed__room', 'doctor')
    except PatientProfile.DoesNotExist:
        if request.user.role in ['ADMIN', 'RECEPTIONIST', 'DOCTOR']:
            assignments = RoomAssignment.objects.all().select_related('bed__room', 'doctor')
        else:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    total_count = assignments.count()
    
    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_assignments = assignments[start_idx:end_idx]
    
    serializer = RoomAssignmentSerializer(paginated_assignments, many=True)
    
    return Response(
        {
            'count': total_count,
            'next': f'/api/rooms/assignments/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/rooms/assignments/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def room_current_assignment_api(request):
    """Get current active room assignment for a patient"""
    if request.user.role != 'PATIENT':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        from users.models import PatientProfile
        patient = PatientProfile.objects.get(user=request.user)
        assignment = RoomAssignment.objects.filter(
            patient=patient,
            status='ADMITTED'
        ).select_related('bed__room', 'doctor').latest('admitted_at')
        
        serializer = RoomAssignmentSerializer(assignment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except RoomAssignment.DoesNotExist:
        return Response(
            {'detail': 'No active room assignment'},
            status=status.HTTP_404_NOT_FOUND
        )
    except PatientProfile.DoesNotExist:
        return Response(
            {'detail': 'Patient profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def admission_requests_list_api(request):
    """Get admission requests"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10
    
    # Return role-scoped data to avoid leaking unrelated requests.
    from users.models import PatientProfile
    from clinical.models import Doctor
    try:
        patient = PatientProfile.objects.get(user=request.user)
        requests_qs = AdmissionRequest.objects.filter(patient=patient).select_related('doctor', 'preferred_room')
    except PatientProfile.DoesNotExist:
        if request.user.role == 'DOCTOR':
            doctor = getattr(request.user, 'doctor_profile', None)
            if doctor:
                requests_qs = AdmissionRequest.objects.filter(doctor=doctor).select_related('doctor', 'preferred_room')
            else:
                requests_qs = AdmissionRequest.objects.none()
        elif request.user.role in {'ADMIN', 'RECEPTIONIST'}:
            requests_qs = AdmissionRequest.objects.all().select_related('doctor', 'preferred_room')
        else:
            requests_qs = AdmissionRequest.objects.none()
    
    total_count = requests_qs.count()
    
    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_requests = requests_qs[start_idx:end_idx]
    
    serializer = AdmissionRequestSerializer(paginated_requests, many=True)
    
    return Response(
        {
            'count': total_count,
            'next': f'/api/rooms/admission-requests/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/rooms/admission-requests/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def room_book_bed_api(request):
    """Book an available bed for staff roles or create recommendation for doctors."""
    allowed_roles = {'ADMIN', 'DOCTOR', 'RECEPTIONIST'}
    if request.user.role not in allowed_roles:
        return Response({'detail': 'Not allowed to book beds.'}, status=status.HTTP_403_FORBIDDEN)

    patient_id = request.data.get('patient')
    bed_id = request.data.get('bed')
    doctor_id = request.data.get('doctor')
    reason = (request.data.get('reason') or '').strip()

    if not patient_id or not bed_id:
        return Response({'detail': 'patient and bed are required.'}, status=status.HTTP_400_BAD_REQUEST)

    from users.models import PatientProfile
    from clinical.models import Doctor

    try:
        patient_id = int(patient_id)
        bed_id = int(bed_id)
    except (TypeError, ValueError):
        return Response({'detail': 'patient and bed must be valid IDs.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        patient = PatientProfile.objects.get(pk=patient_id)
    except PatientProfile.DoesNotExist:
        return Response({'detail': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

    doctor = None
    if doctor_id not in [None, '']:
        try:
            doctor = Doctor.objects.get(pk=int(doctor_id))
        except (TypeError, ValueError, Doctor.DoesNotExist):
            return Response({'detail': 'Doctor not found.'}, status=status.HTTP_404_NOT_FOUND)
    elif request.user.role == 'DOCTOR':
        doctor = getattr(request.user, 'doctor_profile', None)

    with transaction.atomic():
        # Prevent assigning multiple active beds to same patient.
        existing = RoomAssignment.objects.select_for_update().filter(patient=patient, status='ADMITTED').first()
        if existing:
            return Response(
                {'detail': f'Patient already admitted in room {existing.bed.room.room_number}, bed {existing.bed.bed_number}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            bed = RoomBed.objects.select_for_update().select_related('room').get(pk=bed_id)
        except RoomBed.DoesNotExist:
            return Response({'detail': 'Bed not found.'}, status=status.HTTP_404_NOT_FOUND)

        if bed.status != 'AVAILABLE':
            return Response({'detail': 'Selected bed is not available.'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.role == 'DOCTOR':
            existing_request = AdmissionRequest.objects.select_for_update().filter(
                patient=patient,
                doctor=doctor,
                status='PENDING',
            ).first()
            if existing_request:
                return Response(
                    {'detail': 'A pending bed recommendation already exists for this patient.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            recommendation = AdmissionRequest.objects.create(
                patient=patient,
                doctor=doctor,
                requested_by=request.user,
                preferred_room=bed.room,
                preferred_room_type=bed.room.room_type,
                reason=reason or f'Recommended bed {bed.bed_number} in room {bed.room.room_number}',
                status='PENDING',
            )

            serializer = AdmissionRequestSerializer(recommendation)
            return Response(
                {
                    'mode': 'RECOMMENDATION',
                    'detail': 'Bed recommendation sent to receptionist for processing.',
                    'request': serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        assignment = RoomAssignment.objects.create(
            patient=patient,
            bed=bed,
            admitted_by=request.user,
            doctor=doctor,
            reason=reason,
            status='ADMITTED',
        )

        bed.status = 'OCCUPIED'
        bed.save(update_fields=['status'])

    serializer = RoomAssignmentSerializer(assignment)
    return Response(
        {
            'mode': 'BOOKED',
            'detail': 'Bed booked successfully.',
            'assignment': serializer.data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def room_book_request_api(request):
    """Allow a patient to request one room booking until discharge."""
    if request.user.role != 'PATIENT':
        return Response({'detail': 'Only patients can request room booking.'}, status=status.HTTP_403_FORBIDDEN)

    from users.models import PatientProfile

    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        return Response({'detail': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    room_id = request.data.get('room')
    reason = (request.data.get('reason') or '').strip()
    if not room_id:
        return Response({'detail': 'room is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        room = Room.objects.get(pk=int(room_id), is_active=True)
    except (TypeError, ValueError, Room.DoesNotExist):
        return Response({'detail': 'Room not found.'}, status=status.HTTP_404_NOT_FOUND)

    has_active_assignment = RoomAssignment.objects.filter(patient=patient, status='ADMITTED').exists()
    if has_active_assignment:
        return Response(
            {'detail': 'You are already admitted. You cannot book another room until discharge.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    has_pending_request = AdmissionRequest.objects.filter(patient=patient, status='PENDING').exists()
    if has_pending_request:
        return Response(
            {'detail': 'You already have a pending room booking request.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if RoomBed.objects.filter(room=room, status='AVAILABLE').count() == 0:
        return Response({'detail': 'No available beds in this room.'}, status=status.HTTP_400_BAD_REQUEST)

    request_obj = AdmissionRequest.objects.create(
        patient=patient,
        requested_by=request.user,
        preferred_room=room,
        preferred_room_type=room.room_type,
        reason=reason or f'Patient requested room {room.room_number}',
        status='PENDING',
    )

    serializer = AdmissionRequestSerializer(request_obj)
    return Response(
        {
            'detail': 'Room booking request submitted successfully.',
            'request': serializer.data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def admission_requests_admin_api(request):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    queryset = AdmissionRequest.objects.select_related('patient__user', 'doctor__user', 'preferred_room').order_by('-created_at')
    status_filter = (request.GET.get('status') or '').strip().upper()
    if status_filter in {'PENDING', 'APPROVED', 'REJECTED', 'ADMITTED'}:
        queryset = queryset.filter(status=status_filter)

    serializer = AdmissionRequestAdminSerializer(queryset[:300], many=True)
    return Response({'count': queryset.count(), 'results': serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def admission_request_review_api(request, request_id):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        admission = AdmissionRequest.objects.select_related('patient__user', 'preferred_room').get(pk=request_id)
    except AdmissionRequest.DoesNotExist:
        return Response({'detail': 'Admission request not found.'}, status=status.HTTP_404_NOT_FOUND)

    action = (request.data.get('action') or '').strip().upper()
    notes = (request.data.get('notes') or '').strip()
    if action not in {'APPROVED', 'REJECTED'}:
        return Response({'detail': 'action must be APPROVED or REJECTED.'}, status=status.HTTP_400_BAD_REQUEST)

    if admission.status not in {'PENDING', 'APPROVED'}:
        return Response({'detail': f'Admission request is already {admission.status.lower()}.'}, status=status.HTTP_400_BAD_REQUEST)

    if action == 'REJECTED':
        admission.status = 'REJECTED'
        admission.receptionist_notes = notes or admission.receptionist_notes
        admission.processed_by = request.user
        admission.processed_at = timezone.now()
        admission.save(update_fields=['status', 'receptionist_notes', 'processed_by', 'processed_at'])
        return Response(AdmissionRequestAdminSerializer(admission).data, status=status.HTTP_200_OK)

    preferred_room = admission.preferred_room
    beds = RoomBed.objects.select_for_update().select_related('room').filter(status='AVAILABLE', room__is_active=True)
    if preferred_room:
        beds = beds.filter(room=preferred_room)
    elif admission.preferred_room_type:
        beds = beds.filter(room__room_type=admission.preferred_room_type)

    bed = beds.order_by('room__room_number', 'bed_number').first()
    if not bed:
        return Response({'detail': 'No available bed found for this admission request.'}, status=status.HTTP_409_CONFLICT)

    with transaction.atomic():
        existing = RoomAssignment.objects.select_for_update().filter(patient=admission.patient, status='ADMITTED').first()
        if existing:
            return Response({'detail': 'Patient already has an active room assignment.'}, status=status.HTTP_400_BAD_REQUEST)

        assignment = RoomAssignment.objects.create(
            patient=admission.patient,
            bed=bed,
            admitted_by=request.user,
            doctor=admission.doctor,
            reason=admission.reason,
            status='ADMITTED',
        )
        bed.status = 'OCCUPIED'
        bed.save(update_fields=['status'])

        admission.status = 'ADMITTED'
        admission.receptionist_notes = notes or admission.receptionist_notes
        admission.processed_by = request.user
        admission.processed_at = timezone.now()
        admission.preferred_room = bed.room
        admission.save(update_fields=['status', 'receptionist_notes', 'processed_by', 'processed_at', 'preferred_room'])

    return Response({
        'admission': AdmissionRequestAdminSerializer(admission).data,
        'assignment': RoomAssignmentSerializer(assignment).data,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def room_transfers_admin_api(request):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    queryset = RoomTransfer.objects.select_related('patient__user', 'doctor__user', 'from_bed__room', 'to_bed__room').order_by('-requested_at')
    status_filter = (request.GET.get('status') or '').strip().upper()
    if status_filter in {'PENDING', 'APPROVED', 'COMPLETED', 'CANCELLED'}:
        queryset = queryset.filter(status=status_filter)

    serializer = RoomTransferAdminSerializer(queryset[:300], many=True)
    return Response({'count': queryset.count(), 'results': serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def room_transfer_create_api(request):
    if request.user.role not in ['ADMIN', 'DOCTOR', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    patient_id = request.data.get('patient')
    from_bed_id = request.data.get('from_bed')
    to_bed_id = request.data.get('to_bed')
    doctor_id = request.data.get('doctor')
    reason = (request.data.get('reason') or '').strip()
    notes = (request.data.get('notes') or '').strip()

    if not patient_id or not from_bed_id or not to_bed_id:
        return Response({'detail': 'patient, from_bed and to_bed are required.'}, status=status.HTTP_400_BAD_REQUEST)

    from users.models import PatientProfile
    from clinical.models import Doctor

    try:
        patient = PatientProfile.objects.get(pk=int(patient_id))
        from_bed = RoomBed.objects.select_related('room').get(pk=int(from_bed_id))
        to_bed = RoomBed.objects.select_related('room').get(pk=int(to_bed_id))
    except (TypeError, ValueError, PatientProfile.DoesNotExist, RoomBed.DoesNotExist):
        return Response({'detail': 'Invalid patient or bed selected.'}, status=status.HTTP_404_NOT_FOUND)

    doctor = None
    if doctor_id not in [None, '']:
        try:
            doctor = Doctor.objects.get(pk=int(doctor_id))
        except (TypeError, ValueError, Doctor.DoesNotExist):
            return Response({'detail': 'Doctor not found.'}, status=status.HTTP_404_NOT_FOUND)
    elif request.user.role == 'DOCTOR':
        doctor = getattr(request.user, 'doctor_profile', None)

    if from_bed.status != 'OCCUPIED' or to_bed.status != 'AVAILABLE':
        return Response({'detail': 'Selected beds are not in a valid state for transfer.'}, status=status.HTTP_400_BAD_REQUEST)

    transfer = RoomTransfer.objects.create(
        patient=patient,
        from_bed=from_bed,
        to_bed=to_bed,
        doctor=doctor,
        reason=reason or 'Room transfer request',
        status='PENDING',
        notes=notes,
    )
    return Response(RoomTransferAdminSerializer(transfer).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def room_transfer_review_api(request, transfer_id):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        transfer = RoomTransfer.objects.select_related('patient__user', 'from_bed__room', 'to_bed__room').get(pk=transfer_id)
    except RoomTransfer.DoesNotExist:
        return Response({'detail': 'Room transfer not found.'}, status=status.HTTP_404_NOT_FOUND)

    action = (request.data.get('action') or '').strip().upper()
    notes = (request.data.get('notes') or '').strip()
    if action not in {'APPROVED', 'REJECTED'}:
        return Response({'detail': 'action must be APPROVED or REJECTED.'}, status=status.HTTP_400_BAD_REQUEST)

    if transfer.status != 'PENDING':
        return Response({'detail': f'Transfer is already {transfer.status.lower()}.'}, status=status.HTTP_400_BAD_REQUEST)

    if action == 'REJECTED':
        transfer.status = 'CANCELLED'
        if notes:
            transfer.notes = notes
        transfer.save(update_fields=['status', 'notes'])
        return Response(RoomTransferAdminSerializer(transfer).data, status=status.HTTP_200_OK)

    with transaction.atomic():
        assignment = RoomAssignment.objects.select_for_update().filter(patient=transfer.patient, status='ADMITTED').first()
        if not assignment:
            return Response({'detail': 'No active room assignment found for this patient.'}, status=status.HTTP_404_NOT_FOUND)

        if assignment.bed_id != transfer.from_bed_id:
            return Response({'detail': 'Current bed does not match the requested transfer source.'}, status=status.HTTP_400_BAD_REQUEST)

        if transfer.to_bed.status != 'AVAILABLE':
            return Response({'detail': 'Target bed is no longer available.'}, status=status.HTTP_400_BAD_REQUEST)

        old_bed = transfer.from_bed
        new_bed = transfer.to_bed
        old_bed.status = 'AVAILABLE'
        old_bed.save(update_fields=['status'])

        new_bed.status = 'OCCUPIED'
        new_bed.save(update_fields=['status'])

        assignment.bed = new_bed
        assignment.status = 'TRANSFERRED'
        assignment.reason = transfer.reason or assignment.reason
        assignment.save(update_fields=['bed', 'status', 'reason'])

        transfer.status = 'COMPLETED'
        transfer.completed_at = timezone.now()
        if notes:
            transfer.notes = notes
        transfer.save(update_fields=['status', 'completed_at', 'notes'])

    return Response(RoomTransferAdminSerializer(transfer).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def room_statistics_api(request):
    """Admin room statistics summary and per-room metrics."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    rooms = Room.objects.prefetch_related('beds').filter(is_active=True)
    total_beds = sum(room.capacity for room in rooms)
    occupied_beds = RoomBed.objects.filter(status='OCCUPIED', room__is_active=True).count()
    available_beds = RoomBed.objects.filter(status='AVAILABLE', room__is_active=True).count()
    maintenance_beds = RoomBed.objects.filter(status='MAINTENANCE', room__is_active=True).count()

    occupancy_rate = int((occupied_beds / total_beds * 100)) if total_beds > 0 else 0

    room_type_distribution = []
    total_rooms = rooms.count()
    for room_type_val, room_type_label in Room.ROOM_TYPE_CHOICES:
        count = rooms.filter(room_type=room_type_val).count()
        percent = int((count / total_rooms * 100)) if total_rooms > 0 else 0
        room_type_distribution.append(
            {
                'type': room_type_val,
                'label': room_type_label,
                'count': count,
                'percent': percent,
            }
        )

    room_statistics = []
    for room in rooms:
        occupied = room.beds.filter(status='OCCUPIED').count()
        available = room.beds.filter(status='AVAILABLE').count()
        maintenance = room.beds.filter(status='MAINTENANCE').count()
        room_statistics.append(
            {
                'id': room.id,
                'room_number': room.room_number,
                'room_type': room.room_type,
                'floor': room.floor,
                'capacity': room.capacity,
                'occupied_beds_count': occupied,
                'available_beds_count': available,
                'maintenance_beds_count': maintenance,
                'utilization_percent': int((occupied / room.capacity * 100)) if room.capacity > 0 else 0,
            }
        )

    return Response(
        {
            'kpis': {
                'total_rooms': total_rooms,
                'active_rooms': total_rooms,
                'total_beds': total_beds,
                'occupied_beds': occupied_beds,
                'available_beds': available_beds,
                'maintenance_beds': maintenance_beds,
                'occupancy_rate': occupancy_rate,
            },
            'room_type_distribution': room_type_distribution,
            'room_statistics': room_statistics,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def room_statistics_export_csv_api(request):
    """Admin CSV export of room statistics."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    rooms = Room.objects.prefetch_related('beds').filter(is_active=True)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="room_statistics.csv"'
    writer = csv.writer(response)
    writer.writerow(['Room Number', 'Type', 'Floor', 'Capacity', 'Occupied', 'Available', 'Maintenance', 'Utilization %'])

    for room in rooms:
        occupied = room.beds.filter(status='OCCUPIED').count()
        available = room.beds.filter(status='AVAILABLE').count()
        maintenance = room.beds.filter(status='MAINTENANCE').count()
        utilization = int((occupied / room.capacity) * 100) if room.capacity > 0 else 0
        writer.writerow([
            room.room_number,
            room.get_room_type_display(),
            room.floor,
            room.capacity,
            occupied,
            available,
            maintenance,
            utilization,
        ])

    return response
