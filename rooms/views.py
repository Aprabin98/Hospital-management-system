from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from notifications.utils import create_notification

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
