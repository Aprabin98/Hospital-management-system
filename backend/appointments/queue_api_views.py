"""
Phase 2: Queue and receptionist board API views.
Supports token-based check-in, queue management, and no-show recovery.
"""
from datetime import datetime, timedelta

from django.db.models import Case, IntegerField, Value, When
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from appointments.models import Queue, Appointment
from appointments.patient_matcher import PatientMatchingService
from appointments.api_serializers import QueueSerializer
from clinical.models import Doctor
from users.models import PatientProfile


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def queue_list_api(request):
    """
    List queue entries for a doctor (receptionist view) or create new queue entry (walk-in).
    
    GET: List queue entries filtered by doctor and status.
    Query params:
    - doctor_id: Filter by doctor (required for receptionist)
    - status: Filter by status (optional) e.g., 'WAITING', 'CALLED', 'IN_CONSULTATION'
    
    POST: Add patient to queue (walk-in or scheduled).
    Body: {
        "patient_id": int,
        "doctor_id": int,
        "source": "WALK_IN" | "SCHEDULED" | "REFERRAL",
        "appointment_id": int (optional),
        "priority": "P1" | "P2" | "P3" | "P4" (default P4),
        "notes": "string"
    }
    """
    if request.method == 'GET':
        # Receptionist can see queue for their assigned doctor
        if request.user.role not in ['RECEPTIONIST', 'ADMIN', 'DOCTOR']:
            return Response(
                {'detail': 'Only receptionists and doctors can view queue'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        doctor_id = request.GET.get('doctor_id')
        status_filter = request.GET.get('status')

        queue_entries = Queue.objects.select_related(
            'patient__user', 'doctor__user', 'triage_assessment', 'appointment'
        ).all()

        # Doctor users can only see their own queue.
        if request.user.role == 'DOCTOR':
            queue_entries = queue_entries.filter(doctor__user_id=request.user.id)
        elif doctor_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
            except Doctor.DoesNotExist:
                return Response({'detail': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
            queue_entries = queue_entries.filter(doctor=doctor)

        if status_filter:
            statuses = [s.strip().upper() for s in status_filter.split(',') if s.strip()]
            queue_entries = queue_entries.filter(status__in=statuses)
        else:
            queue_entries = queue_entries.filter(status__in=['WAITING', 'CALLED', 'IN_CONSULTATION'])

        queue_entries = queue_entries.annotate(
            priority_rank=Case(
                When(priority='P1', then=Value(1)),
                When(priority='P2', then=Value(2)),
                When(priority='P3', then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            )
        ).order_by('priority_rank', 'queued_at')
        
        serializer = QueueSerializer(queue_entries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Add patient to queue
        if request.user.role not in ['RECEPTIONIST', 'ADMIN']:
            return Response(
                {'detail': 'Only receptionists can add to queue'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient_id = request.data.get('patient_id')
            doctor_id = request.data.get('doctor_id')
            source = request.data.get('source', 'SCHEDULED')
            appointment_id = request.data.get('appointment_id')
            priority = request.data.get('priority', 'P4')
            notes = request.data.get('notes', '')

            if not patient_id or not doctor_id:
                return Response(
                    {'detail': 'patient_id and doctor_id are required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            patient = PatientProfile.objects.get(id=patient_id)
            doctor = Doctor.objects.get(id=doctor_id)

            if Queue.objects.filter(
                patient=patient,
                doctor=doctor,
                status__in=['WAITING', 'CALLED', 'IN_CONSULTATION']
            ).exists():
                return Response(
                    {'detail': 'Patient is already in active queue for this doctor'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            appointment = None
            if appointment_id:
                appointment = Appointment.objects.get(id=appointment_id)
            
            # Create queue entry
            queue_entry = Queue.objects.create(
                patient=patient,
                doctor=doctor,
                appointment=appointment,
                source=source,
                priority=priority,
                notes=notes,
            )
            
            serializer = QueueSerializer(queue_entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except PatientProfile.DoesNotExist:
            return Response({'detail': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        except Doctor.DoesNotExist:
            return Response({'detail': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        except Appointment.DoesNotExist:
            return Response({'detail': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {'detail': f'Error creating queue entry: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def queue_update_status_api(request, queue_id):
    """
    Update queue entry status (call patient, mark consultation start/end, no-show).
    
    PATCH body: {
        "status": "CALLED" | "IN_CONSULTATION" | "COMPLETED" | "NO_SHOW" | "ARCHIVED",
        "no_show_reason": "string" (required if status is NO_SHOW),
        "notes": "string"
    }
    """
    if request.user.role not in ['RECEPTIONIST', 'ADMIN', 'DOCTOR']:
        return Response(
            {'detail': 'Only receptionists and doctors can update queue'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        queue_entry = Queue.objects.get(id=queue_id)
    except Queue.DoesNotExist:
        return Response({'detail': 'Queue entry not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check authorization
    if request.user.role == 'DOCTOR' and queue_entry.doctor.user_id != request.user.id:
        return Response(
            {'detail': 'Can only update your own queue'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        new_status = (request.data.get('status') or '').upper()
        allowed_statuses = {'CALLED', 'IN_CONSULTATION', 'COMPLETED', 'NO_SHOW', 'ARCHIVED'}
        if new_status not in allowed_statuses:
            return Response(
                {'detail': f'Invalid status. Allowed: {", ".join(sorted(allowed_statuses))}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_status == 'CALLED':
            if not queue_entry.called_at:
                queue_entry.called_at = timezone.now()
            queue_entry.status = 'CALLED'
        
        elif new_status == 'IN_CONSULTATION':
            now = timezone.now()
            if not queue_entry.called_at:
                queue_entry.called_at = now
            if not queue_entry.consultation_start:
                queue_entry.consultation_start = now
            queue_entry.status = 'IN_CONSULTATION'
        
        elif new_status == 'COMPLETED':
            now = timezone.now()
            if not queue_entry.consultation_start:
                queue_entry.consultation_start = queue_entry.called_at or now
            queue_entry.consultation_end = now
            queue_entry.status = 'COMPLETED'
            # Also mark appointment as completed
            if queue_entry.appointment:
                queue_entry.appointment.status = 'COMPLETED'
                queue_entry.appointment.save()
        
        elif new_status == 'NO_SHOW':
            queue_entry.status = 'NO_SHOW'
            no_show_reason = (request.data.get('no_show_reason') or '').strip()
            if no_show_reason:
                queue_entry.no_show_reason = no_show_reason
            # Mark appointment as no-show
            if queue_entry.appointment:
                queue_entry.appointment.status = 'NO_SHOW'
                queue_entry.appointment.save()
        
        elif new_status == 'ARCHIVED':
            queue_entry.status = 'ARCHIVED'
        
        if request.data.get('notes'):
            queue_entry.notes = request.data.get('notes')
        
        queue_entry.save()
        serializer = QueueSerializer(queue_entry)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'detail': f'Error updating queue: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_duplicate_patient_api(request):
    """
    Check for duplicate patients during walk-in registration.
    
    Query params:
    - full_name: Patient full name (required)
    - date_of_birth: Date of birth YYYY-MM-DD (required)
    - phone: Phone number (optional)
    - email: Email address (optional)
    
    Returns:
    {
        "matches": [
            {
                "patient_id": int,
                "patient_name": str,
                "match_type": str,
                "confidence": float,
                "patient_details": {...}
            }
        ]
    }
    """
    if request.user.role != 'RECEPTIONIST' and request.user.role != 'ADMIN':
        return Response(
            {'detail': 'Only receptionists can check duplicates'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    full_name = request.GET.get('full_name')
    dob_str = request.GET.get('date_of_birth')
    phone = request.GET.get('phone')
    email = request.GET.get('email')
    
    if not full_name or not dob_str:
        return Response(
            {'detail': 'full_name and date_of_birth required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from datetime import datetime
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {'detail': 'Invalid date format. Use YYYY-MM-DD'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    matches = PatientMatchingService.find_potential_matches(
        full_name=full_name,
        date_of_birth=dob,
        phone=phone,
        email=email
    )
    
    result = {
        'matches': [
            {
                'patient_id': patient.id,
                'patient_name': patient.full_name,
                'date_of_birth': patient.date_of_birth,
                'phone': patient.phone,
                'email': patient.user.email,
                'match_type': match_type,
                'confidence': float(confidence),
            }
            for patient, match_type, confidence in matches
        ]
    }
    
    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def no_show_rebook_api(request, queue_id):
    """
    Handle no-show patient rebooking workflow.
    
    POST body: {
        "rebook_date": "YYYY-MM-DD",
        "rebook_time": "HH:MM",
        "contact_attempts": int,
        "contact_notes": "string"
    }
    """
    if request.user.role not in ['RECEPTIONIST', 'ADMIN']:
        return Response(
            {'detail': 'Only receptionists can rebook'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        queue_entry = Queue.objects.get(id=queue_id)
        
        if queue_entry.status != 'NO_SHOW':
            return Response(
                {'detail': 'Can only rebook no-show patients'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rebook_date_str = request.data.get('rebook_date')
        rebook_time_str = request.data.get('rebook_time')
        
        if rebook_date_str and rebook_time_str:
            rebook_date = datetime.strptime(rebook_date_str, '%Y-%m-%d').date()
            rebook_time = datetime.strptime(rebook_time_str, '%H:%M').time()

            duration_minutes = 30
            if queue_entry.appointment and queue_entry.appointment.start_time and queue_entry.appointment.end_time:
                start_dt = datetime.combine(rebook_date, queue_entry.appointment.start_time)
                end_dt = datetime.combine(rebook_date, queue_entry.appointment.end_time)
                diff = int((end_dt - start_dt).total_seconds() // 60)
                if diff > 0:
                    duration_minutes = diff

            end_time = (datetime.combine(rebook_date, rebook_time) + timedelta(minutes=duration_minutes)).time()
            
            # Create new appointment
            new_appointment = Appointment.objects.create(
                patient=queue_entry.patient,
                doctor=queue_entry.doctor,
                date=rebook_date,
                start_time=rebook_time,
                end_time=end_time,
                status='PENDING',
                notes=f"Rebooked from no-show on {queue_entry.queued_at.date()}"
            )
            
            # Create new queue entry
            new_queue = Queue.objects.create(
                patient=queue_entry.patient,
                doctor=queue_entry.doctor,
                appointment=new_appointment,
                source=queue_entry.source,
                priority=queue_entry.priority,
                notes=f"Rebooked: {request.data.get('contact_notes', '')}"
            )
            
            queue_entry.rebooking_attempted = True
            queue_entry.rebooking_contact_date = timezone.now()
            queue_entry.save()
            
            serializer = QueueSerializer(new_queue)
            return Response(
                {
                    'message': 'Patient rebooked successfully',
                    'new_appointment_id': new_appointment.id,
                    'new_queue_id': new_queue.id,
                    'new_queue': serializer.data,
                },
                status=status.HTTP_201_CREATED
            )
        else:
            # Just mark as attempted to contact
            queue_entry.rebooking_attempted = True
            queue_entry.rebooking_contact_date = timezone.now()
            queue_entry.notes = request.data.get('contact_notes', '')
            queue_entry.save()
            
            return Response(
                {
                    'message': 'Contact recorded, awaiting rebook confirmation',
                    'queue': QueueSerializer(queue_entry).data,
                },
                status=status.HTTP_200_OK
            )
    
    except Queue.DoesNotExist:
        return Response({'detail': 'Queue entry not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
