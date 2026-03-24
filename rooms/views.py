from django.contrib import messages
from django.contrib.auth.decorators import login_required
import csv
from django.db import transaction
from django.db.models import Q, Count, F, Case, When, IntegerField, Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import json

from notifications.utils import create_notification
from clinical.models import Doctor
from django.contrib.auth import get_user_model
from users.models import PatientProfile

from .forms import DoctorAdmissionRequestForm, RoomAssignmentForm, RoomBedForm, RoomDischargeForm, RoomForm
from .models import AdmissionRequest, Room, RoomAssignment, RoomBed


ALLOWED_ROLES = ['ADMIN', 'RECEPTIONIST']
User = get_user_model()


def _check_role(user):
    return user.role in ALLOWED_ROLES


@login_required
def room_list(request):
    if not _check_role(request.user):
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    query = request.GET.get('q', '').strip()
    rooms = Room.objects.prefetch_related('beds').all().order_by('room_number')
    if query:
        rooms = rooms.filter(Q(room_number__icontains=query) | Q(room_type__icontains=query) | Q(floor__icontains=query))

    return render(request, 'rooms/room_list.html', {'rooms': rooms, 'query': query})


@login_required
def room_create(request):
    if not _check_role(request.user):
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    form = RoomForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        room = form.save()
        for i in range(1, room.capacity + 1):
            RoomBed.objects.create(room=room, bed_number=str(i))
        messages.success(request, 'Room created successfully with beds.')
        return redirect('rooms:room_list')

    return render(request, 'rooms/room_form.html', {'form': form, 'title': 'Create Room'})


@login_required
def room_edit(request, pk):
    if not _check_role(request.user):
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    room = get_object_or_404(Room, pk=pk)
    old_capacity = room.capacity
    form = RoomForm(request.POST or None, instance=room)

    if request.method == 'POST' and form.is_valid():
        room = form.save()
        if room.capacity > old_capacity:
            for i in range(old_capacity + 1, room.capacity + 1):
                RoomBed.objects.get_or_create(room=room, bed_number=str(i))
        messages.success(request, 'Room updated successfully.')
        return redirect('rooms:room_list')

    return render(request, 'rooms/room_form.html', {'form': form, 'title': 'Edit Room', 'room': room})


@login_required
def room_bed_edit(request, room_pk, bed_pk):
    if not _check_role(request.user):
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    room = get_object_or_404(Room, pk=room_pk)
    bed = get_object_or_404(RoomBed, pk=bed_pk, room=room)
    form = RoomBedForm(request.POST or None, instance=bed)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Bed updated.')
        return redirect('rooms:room_detail', pk=room.pk)

    return render(request, 'rooms/bed_form.html', {'form': form, 'room': room, 'bed': bed})


@login_required
def room_detail(request, pk):
    if not _check_role(request.user):
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    room = get_object_or_404(Room.objects.prefetch_related('beds'), pk=pk)
    active_assignments = RoomAssignment.objects.filter(bed__room=room, status='ADMITTED').select_related('patient', 'doctor__user', 'bed')

    return render(request, 'rooms/room_detail.html', {
        'room': room,
        'active_assignments': active_assignments,
    })


@login_required
def admit_patient(request):
    if not _check_role(request.user):
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    form = RoomAssignmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        assignment = form.save(commit=False)

        has_active = RoomAssignment.objects.filter(patient=assignment.patient, status='ADMITTED').exists()
        if has_active:
            messages.error(request, 'This patient already has an active room assignment.')
            return redirect('rooms:admit_patient')

        assignment.admitted_by = request.user
        assignment.save()

        assignment.bed.status = 'OCCUPIED'
        assignment.bed.save(update_fields=['status'])

        if assignment.patient.user_id:
            create_notification(
                recipient=assignment.patient.user,
                title='Room Assigned',
                message=f'You have been admitted to Room {assignment.bed.room.room_number}, Bed {assignment.bed.bed_number}.',
                notification_type='ROOM',
            )

        messages.success(request, 'Patient admitted successfully.')
        return redirect('rooms:active_assignments')

    return render(request, 'rooms/admit_patient.html', {'form': form})


@login_required
def active_assignments(request):
    if not _check_role(request.user):
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    assignments = RoomAssignment.objects.filter(status='ADMITTED').select_related('patient', 'doctor__user', 'bed__room').order_by('-admitted_at')
    return render(request, 'rooms/active_assignments.html', {'assignments': assignments})


@login_required
def discharge_patient(request, pk):
    if not _check_role(request.user):
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    assignment = get_object_or_404(RoomAssignment, pk=pk, status='ADMITTED')
    form = RoomDischargeForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        assignment.status = 'DISCHARGED'
        assignment.discharge_notes = form.cleaned_data.get('discharge_notes', '')
        assignment.discharged_at = timezone.now()
        assignment.save(update_fields=['status', 'discharge_notes', 'discharged_at'])

        assignment.bed.status = 'AVAILABLE'
        assignment.bed.save(update_fields=['status'])

        if assignment.patient.user_id:
            create_notification(
                recipient=assignment.patient.user,
                title='Discharge Completed',
                message='You have been discharged successfully. Please collect your summary from reception.',
                notification_type='ROOM',
            )

        messages.success(request, 'Patient discharged successfully.')
        return redirect('rooms:active_assignments')

    return render(request, 'rooms/discharge_patient.html', {'assignment': assignment, 'form': form})


# ===============================================
# ROLE-BASED DASHBOARD & NEW VIEWS
# ===============================================

@login_required
def room_dashboard(request):
    """Main room management dashboard with role-based options"""
    return render(request, 'rooms/room_dashboard.html')


# ===============================================
# PATIENT VIEWS - Room Booking
# ===============================================

@login_required
def patient_available_rooms(request):
    """Patient view to see and request available rooms"""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied. Patients only.')
        return redirect('users:dashboard')

    # Filter by room type and floor if requested
    rooms = Room.objects.prefetch_related('beds').filter(is_active=True)
    
    room_type = request.GET.get('room_type')
    floor = request.GET.get('floor')
    
    if room_type:
        rooms = rooms.filter(room_type=room_type)
    if floor:
        rooms = rooms.filter(floor__icontains=floor)
    
    # Add available beds count to each room
    available_rooms = []
    for room in rooms:
        available_beds = [bed for bed in room.beds.all() if bed.status == 'AVAILABLE']
        if available_beds:
            room.available_bed_list = available_beds
            room.available_beds_count = len(available_beds)
            room.get_estimated_cost = 5000  # Standard cost per day (can vary by type)
            available_rooms.append(room)
    
    # Get patient's current bookings
    patient = request.user.patient_profile
    patient_bookings = RoomAssignment.objects.filter(patient=patient).select_related('bed__room')
    
    context = {
        'available_rooms': available_rooms,
        'patient_bookings': patient_bookings,
    }
    return render(request, 'rooms/patient_available_rooms.html', context)


@login_required
def patient_book_room(request):
    """Patient books a room"""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        room = get_object_or_404(Room, id=room_id, is_active=True)
        patient = request.user.patient_profile

        has_active = RoomAssignment.objects.filter(patient=patient, status='ADMITTED').exists()
        if has_active:
            messages.error(request, 'You already have an active room assignment.')
            return redirect('rooms:patient_available_rooms')

        has_pending = AdmissionRequest.objects.filter(patient=patient, status='PENDING').exists()
        if has_pending:
            messages.error(request, 'You already have a pending room request.')
            return redirect('rooms:patient_available_rooms')

        reason = request.POST.get('reason', '').strip() or 'Patient requested room booking'
        AdmissionRequest.objects.create(
            patient=patient,
            requested_by=request.user,
            preferred_room=room,
            preferred_room_type=room.room_type,
            reason=reason,
            status='PENDING',
        )

        for recipient in User.objects.filter(role__in=['RECEPTIONIST', 'ADMIN'], is_active=True):
            create_notification(
                recipient=recipient,
                title='New Room Request',
                message=f'{patient.full_name} requested room booking preference: Room {room.room_number}.',
                notification_type='ROOM',
            )

        messages.success(request, 'Room request submitted successfully. Receptionist will confirm your assignment.')
        create_notification(
            recipient=request.user,
            title='Room Request Submitted',
            message=f'Your request for Room {room.room_number} has been submitted for review.',
            notification_type='ROOM',
        )
        
        return redirect('rooms:patient_available_rooms')
    
    messages.error(request, 'Invalid request.')
    return redirect('rooms:patient_available_rooms')


# ===============================================
# DOCTOR VIEWS - Patient Transfer
# ===============================================

@login_required
def doctor_patient_transfers(request):
    """Doctor view to see their patients and transfer them"""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied. Doctors only.')
        return redirect('users:dashboard')
    
    doctor = request.user.doctor_profile
    
    # Get doctor's current patients
    doctor_patients = RoomAssignment.objects.filter(
        doctor=doctor, 
        status='ADMITTED'
    ).select_related('patient__user', 'bed__room').order_by('-admitted_at')
    
    # Get available rooms for transfer
    available_rooms = Room.objects.filter(is_active=True).prefetch_related('beds')
    
    # Get recent transfers by this doctor
    recent_transfers = RoomAssignment.objects.filter(
        doctor=doctor,
        status='ADMITTED'
    ).order_by('-admitted_at')[:10]
    
    context = {
        'doctor_patients': doctor_patients,
        'available_rooms': available_rooms,
        'recent_transfers': recent_transfers,
    }
    return render(request, 'rooms/doctor_patient_transfers.html', context)


@login_required
def doctor_transfer_patient(request):
    """Doctor transfers patient to different room"""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        assignment_id = request.POST.get('assignment_id')
        new_room_id = request.POST.get('new_room_id')
        transfer_reason = request.POST.get('transfer_reason', '')
        
        assignment = get_object_or_404(RoomAssignment, id=assignment_id, status='ADMITTED')
        new_room = get_object_or_404(Room, id=new_room_id)
        
        # Get available bed in new room
        new_bed = new_room.beds.filter(status='AVAILABLE').first()
        if not new_bed:
            messages.error(request, 'No available beds in selected room.')
            return redirect('rooms:doctor_patient_transfers')
        
        # Free up old bed
        old_bed = assignment.bed
        old_bed.status = 'AVAILABLE'
        old_bed.save()
        
        # Assign new bed
        assignment.bed = new_bed
        assignment.save()
        
        new_bed.status = 'OCCUPIED'
        new_bed.save()
        
        # Notify patient
        create_notification(
            recipient=assignment.patient.user,
            title='Room Transfer',
            message=f'You have been transferred to Room {new_room.room_number}, {new_bed.bed_number}. Reason: {transfer_reason}',
            notification_type='ROOM',
        )
        
        messages.success(request, f'Patient transferred to Room {new_room.room_number}.')
    
    return redirect('rooms:doctor_patient_transfers')


@login_required
def doctor_admission_requests(request):
    """Doctor submits admission requests for receptionist processing."""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied. Doctors only.')
        return redirect('users:dashboard')

    doctor = request.user.doctor_profile
    form = DoctorAdmissionRequestForm(request.POST or None, doctor=doctor)

    if request.method == 'POST' and form.is_valid():
        patient = form.cleaned_data['patient']

        has_active = RoomAssignment.objects.filter(
            patient=patient,
            status='ADMITTED'
        ).exists()
        if has_active:
            messages.error(request, 'This patient already has an active room assignment.')
            return redirect('rooms:doctor_admission_requests')

        request_exists = AdmissionRequest.objects.filter(
            patient=patient,
            doctor=doctor,
            status='PENDING'
        ).exists()
        if request_exists:
            messages.error(request, 'A pending admission request already exists for this patient.')
            return redirect('rooms:doctor_admission_requests')

        admission_request = form.save(commit=False)
        admission_request.doctor = doctor
        admission_request.requested_by = request.user
        admission_request.save()

        for recipient in User.objects.filter(role__in=['RECEPTIONIST', 'ADMIN'], is_active=True):
            create_notification(
                recipient=recipient,
                title='New Admission Request',
                message=(
                    f"Dr. {doctor.user.username} requested admission for "
                    f"{patient.full_name}."
                ),
                notification_type='ROOM',
            )

        messages.success(request, 'Admission request submitted. Receptionist will assign room and bed.')
        return redirect('rooms:doctor_admission_requests')

    my_requests = AdmissionRequest.objects.filter(
        doctor=doctor
    ).select_related('patient__user', 'processed_by').order_by('-created_at')

    return render(request, 'rooms/doctor_admission_requests.html', {
        'form': form,
        'my_requests': my_requests,
    })


# ===============================================
# RECEPTIONIST VIEWS - Room Assignment & Occupancy
# ===============================================

@login_required
def receptionist_assign_room(request):
    """Receptionist assigns room to patient"""
    if request.user.role != 'RECEPTIONIST':
        messages.error(request, 'Access denied. Receptionists only.')
        return redirect('users:dashboard')
    
    doctors = Doctor.objects.all().select_related('user')
    available_rooms = Room.objects.filter(is_active=True).prefetch_related('beds')
    for room in available_rooms:
        room.available_beds_count = room.beds.filter(status='AVAILABLE').count()

    pending_requests = AdmissionRequest.objects.filter(
        status='PENDING'
    ).select_related('patient__user', 'doctor__user', 'preferred_room').order_by('created_at')

    today_admissions = RoomAssignment.objects.filter(
        admitted_at__date=timezone.now().date()
    ).select_related('patient__user', 'doctor__user', 'bed__room')
    
    # Prepare room beds JSON for frontend
    room_beds = {}
    for room in available_rooms:
        room_beds[str(room.id)] = [
            {
                'id': bed.id,
                'bed_number': bed.bed_number,
                'status': bed.status
            }
            for bed in room.beds.all()
        ]
    
    # Room type statistics
    stats = {
        'general_available': RoomBed.objects.filter(room__room_type='GENERAL', room__is_active=True, status='AVAILABLE').count(),
        'semi_private_available': RoomBed.objects.filter(room__room_type='SEMI_PRIVATE', room__is_active=True, status='AVAILABLE').count(),
        'private_available': RoomBed.objects.filter(room__room_type='PRIVATE', room__is_active=True, status='AVAILABLE').count(),
        'icu_available': RoomBed.objects.filter(room__room_type='ICU', room__is_active=True, status='AVAILABLE').count(),
        'general_total': RoomBed.objects.filter(room__room_type='GENERAL', room__is_active=True).count(),
        'semi_private_total': RoomBed.objects.filter(room__room_type='SEMI_PRIVATE', room__is_active=True).count(),
        'private_total': RoomBed.objects.filter(room__room_type='PRIVATE', room__is_active=True).count(),
        'icu_total': RoomBed.objects.filter(room__room_type='ICU', room__is_active=True).count(),
    }
    
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        room_id = request.POST.get('room_id')
        bed_id = request.POST.get('bed_id')
        doctor_id = request.POST.get('doctor_id')
        admission_notes = request.POST.get('admission_notes', '')
        request_id = request.POST.get('request_id')
        
        try:
            if not all([patient_id, room_id, bed_id, doctor_id]):
                raise ValueError('Please select patient, room, bed, and doctor.')

            with transaction.atomic():
                patient = PatientProfile.objects.select_for_update().get(id=patient_id)
                doctor = Doctor.objects.get(id=doctor_id)
                bed = RoomBed.objects.select_for_update().select_related('room').get(id=bed_id, room_id=room_id)

                if bed.status != 'AVAILABLE':
                    raise ValueError('Selected bed is no longer available. Please choose another bed.')

                has_active = RoomAssignment.objects.select_for_update().filter(
                    patient=patient,
                    status='ADMITTED'
                ).exists()
                if has_active:
                    raise ValueError('This patient already has an active room assignment.')

                assignment = RoomAssignment.objects.create(
                    patient=patient,
                    bed=bed,
                    doctor=doctor,
                    admitted_by=request.user,
                    reason=admission_notes,
                )

                bed.status = 'OCCUPIED'
                bed.save(update_fields=['status'])
            
            # Notify patient
            create_notification(
                recipient=patient.user,
                title='Room Assigned',
                message=f'You have been admitted to Room {bed.room.room_number}, {bed.bed_number}.',
                notification_type='ROOM',
            )

            if request_id:
                admission_request = AdmissionRequest.objects.filter(
                    id=request_id,
                    status='PENDING'
                ).first()
                if admission_request:
                    if admission_request.patient_id != patient.id:
                        raise ValueError('Request patient does not match selected patient.')

                    admission_request.status = 'APPROVED'
                    admission_request.processed_by = request.user
                    admission_request.processed_at = timezone.now()
                    admission_request.receptionist_notes = admission_notes
                    admission_request.save(update_fields=[
                        'status', 'processed_by', 'processed_at', 'receptionist_notes'
                    ])

                    approval_message = (
                        f"Admission request for {admission_request.patient.full_name} "
                        f"was approved and assigned to Room {bed.room.room_number}, Bed {bed.bed_number}."
                    )
                    recipients = {patient.user_id}
                    create_notification(
                        recipient=patient.user,
                        title='Admission Request Approved',
                        message=approval_message,
                        notification_type='ROOM',
                    )

                    if admission_request.doctor_id and admission_request.doctor.user_id not in recipients:
                        recipients.add(admission_request.doctor.user_id)
                        create_notification(
                            recipient=admission_request.doctor.user,
                            title='Admission Request Approved',
                            message=approval_message,
                            notification_type='ROOM',
                        )

                    if admission_request.requested_by_id and admission_request.requested_by_id not in recipients:
                        create_notification(
                            recipient=admission_request.requested_by,
                            title='Admission Request Approved',
                            message=approval_message,
                            notification_type='ROOM',
                        )
            
            messages.success(request, f'Patient admitted to Room {bed.room.room_number}.')
            return redirect('rooms:receptionist_assign_room')
        
        except Exception as e:
            messages.error(request, f'Error assigning room: {str(e)}')
    
    context = {
        'doctors': doctors,
        'available_rooms': available_rooms,
        'room_beds_json': room_beds,
        'today_admissions': today_admissions,
        'pending_requests': pending_requests,
        'stats': stats,
    }
    return render(request, 'rooms/receptionist_assign_room.html', context)


@login_required
@require_POST
def receptionist_reject_admission_request(request, pk):
    """Receptionist rejects a pending doctor admission request."""
    if request.user.role != 'RECEPTIONIST':
        messages.error(request, 'Access denied. Receptionists only.')
        return redirect('users:dashboard')

    admission_request = get_object_or_404(AdmissionRequest, pk=pk, status='PENDING')
    notes = request.POST.get('notes', '').strip()

    admission_request.status = 'REJECTED'
    admission_request.processed_by = request.user
    admission_request.processed_at = timezone.now()
    admission_request.receptionist_notes = notes
    admission_request.save(update_fields=['status', 'processed_by', 'processed_at', 'receptionist_notes'])

    rejection_message = (
        f"Admission request for {admission_request.patient.full_name} was rejected. "
        f"{notes if notes else ''}"
    ).strip()

    recipients = {admission_request.patient.user_id}
    create_notification(
        recipient=admission_request.patient.user,
        title='Admission Request Rejected',
        message=rejection_message,
        notification_type='ROOM',
    )

    if admission_request.doctor_id and admission_request.doctor.user_id not in recipients:
        recipients.add(admission_request.doctor.user_id)
        create_notification(
            recipient=admission_request.doctor.user,
            title='Admission Request Rejected',
            message=rejection_message,
            notification_type='ROOM',
        )

    if admission_request.requested_by_id and admission_request.requested_by_id not in recipients:
        create_notification(
            recipient=admission_request.requested_by,
            title='Admission Request Rejected',
            message=rejection_message,
            notification_type='ROOM',
        )

    messages.success(request, 'Admission request rejected successfully.')
    return redirect('rooms:receptionist_assign_room')


@login_required
def receptionist_patient_search(request):
    """Return patient search results for receptionist room assignment UI."""
    if request.user.role != 'RECEPTIONIST':
        return JsonResponse({'results': []}, status=403)

    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    patients = PatientProfile.objects.select_related('user').filter(
        Q(full_name__icontains=query)
        | Q(user__email__icontains=query)
        | Q(phone__icontains=query)
    ).order_by('full_name')[:20]

    data = {
        'results': [
            {
                'id': patient.id,
                'full_name': patient.full_name,
                'email': patient.user.email,
                'phone': patient.phone or '',
            }
            for patient in patients
        ]
    }
    return JsonResponse(data)


@login_required
def receptionist_occupancy(request):
    """Receptionist views room occupancy report"""
    if request.user.role != 'RECEPTIONIST':
        messages.error(request, 'Access denied. Receptionists only.')
        return redirect('users:dashboard')
    
    rooms = Room.objects.prefetch_related('beds').filter(is_active=True)
    
    # Calculate statistics
    total_beds = sum(room.capacity for room in rooms)
    occupied_beds = RoomBed.objects.filter(status='OCCUPIED').count()
    available_beds = RoomBed.objects.filter(status='AVAILABLE').count()
    maintenance_beds = RoomBed.objects.filter(status='MAINTENANCE').count()
    
    occupancy_percentage = int((occupied_beds / total_beds * 100)) if total_beds > 0 else 0
    
    # Room type statistics
    room_types = Room.ROOM_TYPE_CHOICES
    room_type_stats = []
    for room_type_val, room_type_label in room_types:
        type_rooms = rooms.filter(room_type=room_type_val)
        type_occupied = RoomBed.objects.filter(
            room__in=type_rooms, status='OCCUPIED'
        ).count()
        type_total = RoomBed.objects.filter(
            room__in=type_rooms
        ).count()
        occupancy_percent = int((type_occupied / type_total * 100)) if type_total > 0 else 0
        
        room_type_stats.append({
            'type': room_type_val,
            'type_display': room_type_label,
            'occupied': type_occupied,
            'total': type_total,
            'occupancy_percent': occupancy_percent,
        })
    
    # Floor statistics
    floors = rooms.values_list('floor', flat=True).distinct()
    floor_stats = []
    for floor in floors:
        floor_rooms = rooms.filter(floor=floor)
        floor_occupied = RoomBed.objects.filter(
            room__in=floor_rooms, status='OCCUPIED'
        ).count()
        floor_available = RoomBed.objects.filter(
            room__in=floor_rooms, status='AVAILABLE'
        ).count()
        floor_total = RoomBed.objects.filter(
            room__in=floor_rooms
        ).count()
        floor_occupancy_percent = int((floor_occupied / floor_total * 100)) if floor_total > 0 else 0
        
        floor_stats.append({
            'floor': floor,
            'room_count': floor_rooms.count(),
            'total_beds': floor_total,
            'occupied_beds': floor_occupied,
            'available_beds': floor_available,
            'occupancy_percent': floor_occupancy_percent,
        })
    
    # Enhance rooms with bed counts
    for room in rooms:
        room.occupied_beds_count = room.beds.filter(status='OCCUPIED').count()
        room.available_beds_count = room.beds.filter(status='AVAILABLE').count()
        room.maintenance_beds_count = room.beds.filter(status='MAINTENANCE').count()
    
    context = {
        'stats': {
            'occupied_beds': occupied_beds,
            'available_beds': available_beds,
            'maintenance_beds': maintenance_beds,
            'occupancy_percentage': occupancy_percentage,
            'total_rooms': rooms.count(),
            'total_beds': total_beds,
        },
        'room_type_stats': room_type_stats,
        'floor_stats': floor_stats,
        'rooms': rooms,
        'available_floors': sorted(set(floors)),
    }
    return render(request, 'rooms/receptionist_occupancy.html', context)


# ===============================================
# ADMIN VIEWS - Room Statistics
# ===============================================

@login_required
def room_statistics(request):
    """Admin view for room statistics and analytics"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admins only.')
        return redirect('users:dashboard')
    
    rooms = Room.objects.prefetch_related('beds').filter(is_active=True)
    
    # KPIs
    total_beds = sum(room.capacity for room in rooms)
    occupied_beds = RoomBed.objects.filter(status='OCCUPIED').count()
    available_beds = RoomBed.objects.filter(status='AVAILABLE').count()
    maintenance_beds = RoomBed.objects.filter(status='MAINTENANCE').count()
    
    occupancy_rate = int((occupied_beds / total_beds * 100)) if total_beds > 0 else 0
    
    kpis = {
        'total_rooms': rooms.count(),
        'active_rooms': rooms.filter(is_active=True).count(),
        'total_beds': total_beds,
        'total_capacity': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'maintenance_beds': maintenance_beds,
        'occupancy_rate': occupancy_rate,
        'avg_stay_days': 5,  # Would be calculated from actual data
    }
    
    # Room type distribution
    room_types = Room.ROOM_TYPE_CHOICES
    room_type_distribution = []
    total_rooms = rooms.count()
    color_classes = ['text-primary', 'text-success', 'text-danger', 'text-warning', 'text-info']
    for index, (room_type_val, room_type_label) in enumerate(room_types):
        count = rooms.filter(room_type=room_type_val).count()
        percent = int((count / total_rooms * 100)) if total_rooms > 0 else 0
        room_type_distribution.append({
            'label': room_type_label,
            'count': count,
            'percent': percent,
            'color_class': color_classes[index % len(color_classes)],
        })
    
    # Enhance rooms with statistics
    for room in rooms:
        room.occupied_beds_count = room.beds.filter(status='OCCUPIED').count()
        room.available_beds_count = room.beds.filter(status='AVAILABLE').count()
        room.maintenance_beds_count = room.beds.filter(status='MAINTENANCE').count()
        room.utilization_percent = int((room.occupied_beds_count / room.capacity * 100)) if room.capacity > 0 else 0
        room.avg_occupancy_days = 3  # Would be calculated from actual data
    
    # Percentage calculations
    occupied_percent = occupancy_rate
    available_percent = int((available_beds / total_beds * 100)) if total_beds > 0 else 0
    maintenance_percent = int((maintenance_beds / total_beds * 100)) if total_beds > 0 else 0
    
    context = {
        'kpis': kpis,
        'room_type_distribution': room_type_distribution,
        'room_statistics': rooms,
        'occupied_percent': occupied_percent,
        'available_percent': available_percent,
        'maintenance_percent': maintenance_percent,
    }
    return render(request, 'rooms/room_statistics.html', context)


@login_required
def room_statistics_export_csv(request):
    """Export room statistics for admin/reporting workflows."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admins only.')
        return redirect('users:dashboard')

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


# ===============================================
# API VIEWS - Real-time Room Availability
# ===============================================

@login_required
def api_room_availability(request):
    """API endpoint to get real-time available rooms (no AJAX auth needed for frontend)"""
    room_type = request.GET.get('room_type')
    floor = request.GET.get('floor')
    
    rooms = Room.objects.prefetch_related('beds').filter(
        is_active=True
    ).annotate(
        occupied_count=Count('beds', filter=Q(beds__status='OCCUPIED')),
        available_count=Count('beds', filter=Q(beds__status='AVAILABLE')),
    )
    
    if room_type:
        rooms = rooms.filter(room_type=room_type)
    if floor:
        rooms = rooms.filter(floor__icontains=floor)
    
    # Only include rooms with available beds
    rooms = rooms.filter(available_count__gt=0)
    
    data = {
        'timestamp': timezone.now().isoformat(),
        'rooms': [
            {
                'id': room.id,
                'room_number': room.room_number,
                'room_type': room.room_type,
                'floor': room.floor,
                'total_beds': room.capacity,
                'occupied_beds': room.occupied_count,
                'available_beds': room.available_count,
                'occupancy_rate': int((room.occupied_count / room.capacity * 100)) if room.capacity > 0 else 0,
                'is_full': room.available_count == 0,
            }
            for room in rooms
        ]
    }
    return JsonResponse(data)


@login_required
def api_room_beds_availability(request, room_id):
    """API endpoint to get available beds for a specific room"""
    room = get_object_or_404(Room, id=room_id, is_active=True)
    
    beds = room.beds.filter(status__in=['AVAILABLE', 'OCCUPIED']).values(
        'id', 'bed_number', 'status'
    )
    
    data = {
        'room_id': room.id,
        'room_number': room.room_number,
        'room_type': room.room_type,
        'floor': room.floor,
        'timestamp': timezone.now().isoformat(),
        'beds': [
            {
                'id': bed['id'],
                'bed_number': bed['bed_number'],
                'status': bed['status'],
                'is_available': bed['status'] == 'AVAILABLE',
            }
            for bed in beds
        ]
    }
    return JsonResponse(data)


@login_required
def api_patient_room_assignments(request):
    """API endpoint to get patient's current room assignments"""
    if request.user.role != 'PATIENT':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    patient = request.user.patient_profile
    assignments = RoomAssignment.objects.filter(
        patient=patient,
        status='ADMITTED'
    ).select_related('bed__room', 'doctor__user').values(
        'id',
        'bed__room__room_number',
        'bed__room__room_type',
        'bed__bed_number',
        'doctor__user__first_name',
        'doctor__user__last_name',
        'admitted_at'
    )
    
    data = {
        'timestamp': timezone.now().isoformat(),
        'assignments': list(assignments)
    }
    return JsonResponse(data)


@login_required 
def api_doctor_patient_occupancy(request):
    """API endpoint showing doctor's admitted patients with real-time room status"""
    if request.user.role != 'DOCTOR':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    doctor = request.user.doctor_profile
    
    # Get all patients currently assigned to this doctor
    assignments = RoomAssignment.objects.filter(
        doctor=doctor,
        status='ADMITTED'
    ).select_related('patient__user', 'bed__room', 'bed').order_by('-admitted_at')
    
    patient_data = []
    for assignment in assignments:
        patient_data.append({
            'assignment_id': assignment.id,
            'patient_name': assignment.patient.full_name,
            'phone': assignment.patient.phone,
            'age': assignment.patient.age if hasattr(assignment.patient, 'age') else None,
            'gender': assignment.patient.gender if hasattr(assignment.patient, 'gender') else None,
            'room_number': assignment.bed.room.room_number,
            'bed_number': assignment.bed.bed_number,
            'room_type': assignment.bed.room.room_type,
            'floor': assignment.bed.room.floor,
            'admitted_at': assignment.admitted_at.isoformat() if assignment.admitted_at else None,
            'bed_status': assignment.bed.status,
        })
    
    data = {
        'timestamp': timezone.now().isoformat(),
        'total_patients': len(patient_data),
        'patients': patient_data,
    }
    return JsonResponse(data)


@login_required
def api_receptionist_bed_status(request):
    """API endpoint for receptionist to get live bed status by room"""
    if request.user.role not in ['RECEPTIONIST', 'ADMIN']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    room_id = request.GET.get('room_id')
    room_type = request.GET.get('room_type')
    
    rooms = Room.objects.prefetch_related('beds').filter(is_active=True)
    
    if room_id:
        rooms = rooms.filter(id=room_id)
    elif room_type:
        rooms = rooms.filter(room_type=room_type)
    
    room_data = []
    for room in rooms:
        beds = []
        for bed in room.beds.all():
            # Get current patient if occupied
            assignment = RoomAssignment.objects.filter(
                bed=bed,
                status='ADMITTED'
            ).select_related('patient__user', 'doctor__user').first()
            
            beds.append({
                'bed_id': bed.id,
                'bed_number': bed.bed_number,
                'status': bed.status,
                'current_patient': {
                    'id': assignment.patient.id,
                    'name': assignment.patient.full_name,
                    'admitted_at': assignment.admitted_at.isoformat() if assignment.admitted_at else None,
                    'doctor': f"{assignment.doctor.user.first_name} {assignment.doctor.user.last_name}",
                } if assignment else None,
            })
        
        room_data.append({
            'room_id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'floor': room.floor,
            'capacity': room.capacity,
            'beds': beds,
            'occupancy': {
                'occupied': sum(1 for b in beds if b['status'] == 'OCCUPIED'),
                'available': sum(1 for b in beds if b['status'] == 'AVAILABLE'),
                'maintenance': sum(1 for b in beds if b['status'] == 'MAINTENANCE'),
            }
        })
    
    return JsonResponse({
        'timestamp': timezone.now().isoformat(),
        'rooms': room_data,
    })
