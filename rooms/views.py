from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, F, Case, When, IntegerField, Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.http import JsonResponse
import json

from notifications.utils import create_notification
from clinical.models import Doctor
from users.models import PatientProfile

from .forms import RoomAssignmentForm, RoomBedForm, RoomDischargeForm, RoomForm
from .models import Room, RoomAssignment, RoomBed


ALLOWED_ROLES = ['ADMIN', 'RECEPTIONIST']


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
    if not request.user.is_patient:
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
            room.available_beds = available_beds
            room.available_beds_count = len(available_beds)
            room.get_estimated_cost = 5000  # Standard cost per day (can vary by type)
            available_rooms.append(room)
    
    # Get patient's current bookings
    patient = request.user.patientprofile
    patient_bookings = RoomAssignment.objects.filter(patient=patient).select_related('bed__room')
    
    context = {
        'available_rooms': available_rooms,
        'patient_bookings': patient_bookings,
    }
    return render(request, 'rooms/patient_available_rooms.html', context)


@login_required
def patient_book_room(request):
    """Patient books a room"""
    if not request.user.is_patient:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        room = get_object_or_404(Room, id=room_id)
        
        # Get first available bed
        bed = room.beds.filter(status='AVAILABLE').first()
        if not bed:
            messages.error(request, 'No available beds in selected room.')
            return redirect('rooms:patient_available_rooms')
        
        # Create a notification instead of immediate assignment
        # (receptionist will process the booking)
        try:
            doctor = Doctor.objects.first()  # Default doctor, will be assigned by receptionist
            assignment = RoomAssignment.objects.create(
                patient=request.user.patientprofile,
                bed=bed,
                doctor=doctor,
                admitted_by=request.user,
            )
            
            messages.success(request, 'Room booking request submitted! Receptionist will confirm shortly.')
            create_notification(
                recipient=request.user,
                title='Room Booking Confirmed',
                message=f'Your room booking for Room {room.room_number} has been submitted.',
                notification_type='ROOM',
            )
        except Exception as e:
            messages.error(request, f'Error booking room: {str(e)}')
        
        return redirect('rooms:patient_available_rooms')
    
    messages.error(request, 'Invalid request.')
    return redirect('rooms:patient_available_rooms')


# ===============================================
# DOCTOR VIEWS - Patient Transfer
# ===============================================

@login_required
def doctor_patient_transfers(request):
    """Doctor view to see their patients and transfer them"""
    if not request.user.is_doctor:
        messages.error(request, 'Access denied. Doctors only.')
        return redirect('users:dashboard')
    
    doctor = request.user.doctor
    
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
    if not request.user.is_doctor:
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


# ===============================================
# RECEPTIONIST VIEWS - Room Assignment & Occupancy
# ===============================================

@login_required
def receptionist_assign_room(request):
    """Receptionist assigns room to patient"""
    if not request.user.is_receptionist:
        messages.error(request, 'Access denied. Receptionists only.')
        return redirect('users:dashboard')
    
    doctors = Doctor.objects.all().select_related('user')
    available_rooms = Room.objects.filter(is_active=True).prefetch_related('beds')
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
        'general_available': Room.objects.filter(room_type='GENERAL', is_active=True).aggregate(
            total=Count('beds', filter=Q(beds__status='AVAILABLE')) * 1
        )['total'] or 0,
        'semi_private_available': 5,
        'private_available': 4,
        'icu_available': 3,
        'general_total': 10,
        'semi_private_total': 5,
        'private_total': 4,
        'icu_total': 3,
    }
    
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        room_id = request.POST.get('room_id')
        bed_id = request.POST.get('bed_id')
        doctor_id = request.POST.get('doctor_id')
        admission_notes = request.POST.get('admission_notes', '')
        
        try:
            patient = PatientProfile.objects.get(id=patient_id)
            bed = RoomBed.objects.get(id=bed_id)
            doctor = Doctor.objects.get(id=doctor_id)
            
            # Create assignment
            assignment = RoomAssignment.objects.create(
                patient=patient,
                bed=bed,
                doctor=doctor,
                admitted_by=request.user,
            )
            
            # Mark bed as occupied
            bed.status = 'OCCUPIED'
            bed.save()
            
            # Notify patient
            create_notification(
                recipient=patient.user,
                title='Room Assigned',
                message=f'You have been admitted to Room {bed.room.room_number}, {bed.bed_number}.',
                notification_type='ROOM',
            )
            
            messages.success(request, f'Patient admitted to Room {bed.room.room_number}.')
            return redirect('rooms:receptionist_assign_room')
        
        except Exception as e:
            messages.error(request, f'Error assigning room: {str(e)}')
    
    context = {
        'doctors': doctors,
        'available_rooms': available_rooms,
        'room_beds_json': json.dumps(room_beds),
        'today_admissions': today_admissions,
        'stats': stats,
    }
    return render(request, 'rooms/receptionist_assign_room.html', context)


@login_required
def receptionist_occupancy(request):
    """Receptionist views room occupancy report"""
    if not request.user.is_receptionist:
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
    if not (request.user.is_admin or request.user.role == 'ADMIN'):
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
    for room_type_val, room_type_label in room_types:
        count = rooms.filter(room_type=room_type_val).count()
        room_type_distribution.append((room_type_label, count))
    
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
