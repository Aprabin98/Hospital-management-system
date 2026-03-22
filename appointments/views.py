from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST
from datetime import date, datetime
import json

from .models import Appointment, WaitingList
from .forms import (
    AppointmentStep1Form, AppointmentStep2Form,
    AppointmentStep3Form, AppointmentStep4Form,
    AppointmentCancelForm
)
from .utils import generate_available_slots, generate_qr_code, generate_appointment_pdf
from clinical.models import Doctor, Specialization
from users.models import PatientProfile


# ─── STEP 1: SELECT SPECIALIZATION ──────────────────────────────────────────

@login_required
def book_step1(request):
    """Step 1 - Patient selects specialization."""
    if request.user.role not in ['PATIENT', 'RECEPTIONIST']:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    # Clear any previous booking session
    for key in ['booking_specialization', 'booking_doctor', 'booking_date']:
        request.session.pop(key, None)

    form = AppointmentStep1Form(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        specialization = form.cleaned_data['specialization']
        request.session['booking_specialization'] = specialization.id
        return redirect('appointments:book_step2')

    return render(request, 'appointments/book_step1.html', {'form': form})


# ─── STEP 2: SELECT DOCTOR ───────────────────────────────────────────────────

@login_required
def book_step2(request):
    """Step 2 - Patient selects doctor."""
    if request.user.role not in ['PATIENT', 'RECEPTIONIST']:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    specialization_id = request.session.get('booking_specialization')
    if not specialization_id:
        messages.error(request, 'Please start from Step 1.')
        return redirect('appointments:book_step1')

    specialization = get_object_or_404(Specialization, id=specialization_id)
    form = AppointmentStep2Form(request.POST or None, specialization=specialization)

    if request.method == 'POST' and form.is_valid():
        doctor = form.cleaned_data['doctor']
        request.session['booking_doctor'] = doctor.id
        return redirect('appointments:book_step3')

    return render(request, 'appointments/book_step2.html', {
        'form': form,
        'specialization': specialization
    })


# ─── STEP 3: SELECT DATE ─────────────────────────────────────────────────────

@login_required
def book_step3(request):
    """Step 3 - Patient selects date."""
    if request.user.role not in ['PATIENT', 'RECEPTIONIST']:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    doctor_id = request.session.get('booking_doctor')
    if not doctor_id:
        messages.error(request, 'Please start from Step 1.')
        return redirect('appointments:book_step1')

    doctor = get_object_or_404(Doctor, id=doctor_id)
    form = AppointmentStep3Form(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        appointment_date = form.cleaned_data['appointment_date']
        request.session['booking_date'] = str(appointment_date)
        return redirect('appointments:book_step4')

    return render(request, 'appointments/book_step3.html', {
        'form': form,
        'doctor': doctor
    })


# ─── STEP 4: SELECT SLOT ─────────────────────────────────────────────────────

@login_required
def book_step4(request):
    """Step 4 - Patient selects time slot and confirms."""
    if request.user.role not in ['PATIENT', 'RECEPTIONIST']:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    doctor_id = request.session.get('booking_doctor')
    booking_date_str = request.session.get('booking_date')

    if not doctor_id or not booking_date_str:
        messages.error(request, 'Please start from Step 1.')
        return redirect('appointments:book_step1')

    doctor = get_object_or_404(Doctor, id=doctor_id)
    booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()

    # Generate available slots
    available_slots = generate_available_slots(doctor, booking_date)

    # Check if waiting list needed
    if not available_slots:
        messages.warning(request, 'No slots available for this date. You can join the waiting list.')

    form = AppointmentStep4Form(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        slot_data = form.cleaned_data['slot']
        notes = form.cleaned_data.get('notes', '')

        try:
            slot = json.loads(slot_data)
            start_time = slot['start']
            end_time = slot['end']
        except (json.JSONDecodeError, KeyError):
            messages.error(request, 'Invalid slot selected. Please try again.')
            return redirect('appointments:book_step4')

        # Get patient profile
        if request.user.role == 'PATIENT':
            patient = request.user.patient_profile
        else:
            patient_id = request.POST.get('patient_id')
            if not patient_id:
                messages.error(request, 'Please select a patient for receptionist booking.')
                return redirect('appointments:book_step4')
            patient = get_object_or_404(PatientProfile, pk=patient_id)

        # RULE 1: Max 2 appointments per day
        daily_count = Appointment.objects.filter(
            patient=patient,
            date=booking_date,
            status__in=['PENDING', 'CONFIRMED']
        ).count()

        if daily_count >= 2:
            messages.error(request, 'You already have 2 appointments on this day. Maximum limit reached.')
            return redirect('appointments:book_step1')

        # RULE 2: Check slot not already taken
        already_booked = Appointment.objects.filter(
            doctor=doctor,
            date=booking_date,
            start_time=start_time,
            status__in=['PENDING', 'CONFIRMED']
        ).exists()

        if already_booked:
            messages.error(request, 'This slot was just taken. Please select another slot.')
            return redirect('appointments:book_step4')

        # CREATE APPOINTMENT
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=booking_date,
            start_time=start_time,
            end_time=end_time,
            status='CONFIRMED',
            notes=notes,
        )

        # Generate QR code first then PDF
        generate_qr_code(appointment)
        generate_appointment_pdf(appointment)
        appointment.save()

        # Clear session
        for key in ['booking_specialization', 'booking_doctor', 'booking_date']:
            request.session.pop(key, None)

        messages.success(request, f'Appointment confirmed! Your appointment ID is #{appointment.id}')
        return redirect('appointments:appointment_detail', pk=appointment.id)

    return render(request, 'appointments/book_step4.html', {
        'form': form,
        'doctor': doctor,
        'booking_date': booking_date,
        'available_slots': available_slots,
        'patients': PatientProfile.objects.select_related('user').order_by('full_name') if request.user.role == 'RECEPTIONIST' else None,
    })


# ─── APPOINTMENT LIST ────────────────────────────────────────────────────────

@login_required
def appointment_list(request):
    """Patient views their appointments."""
    if request.user.role == 'PATIENT':
        appointments = Appointment.objects.filter(
            patient=request.user.patient_profile
        ).select_related('doctor__user', 'doctor__specialization').order_by('-date')

    elif request.user.role == 'DOCTOR':
        appointments = Appointment.objects.filter(
            doctor=request.user.doctor_profile
        ).select_related('patient').order_by('-date', 'start_time')

    elif request.user.role in ['ADMIN', 'RECEPTIONIST']:
        appointments = Appointment.objects.all().select_related(
            'patient', 'doctor__user'
        ).order_by('-date')

    else:
        appointments = []

    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments
    })


# ─── APPOINTMENT DETAIL ──────────────────────────────────────────────────────

@login_required
def appointment_detail(request, pk):
    """View appointment details."""
    appointment = get_object_or_404(
        Appointment.objects.select_related(
            'patient', 'doctor__user', 'doctor__specialization'
        ).prefetch_related('prescription__items'),
        pk=pk,
    )

    # Security - only relevant users can view
    if request.user.role == 'PATIENT':
        if appointment.patient != request.user.patient_profile:
            messages.error(request, 'Access denied.')
            return redirect('appointments:appointment_list')

    elif request.user.role == 'DOCTOR':
        if appointment.doctor != request.user.doctor_profile:
            messages.error(request, 'Access denied.')
            return redirect('appointments:appointment_list')

    prescription = None
    try:
        prescription = appointment.prescription
    except Exception:
        prescription = None

    same_day_appointments = Appointment.objects.filter(
        patient=appointment.patient,
        date=appointment.date,
    ).exclude(pk=appointment.pk).select_related('doctor__user').order_by('start_time')

    return render(request, 'appointments/appointment_detail.html', {
        'appointment': appointment,
        'prescription': prescription,
        'same_day_appointments': same_day_appointments,
    })


# ─── CANCEL APPOINTMENT ──────────────────────────────────────────────────────

@login_required
def cancel_appointment(request, pk):
    """Cancel an appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)

    # Only patient who owns it or admin/receptionist can cancel
    if request.user.role == 'PATIENT':
        if appointment.patient != request.user.patient_profile:
            messages.error(request, 'Access denied.')
            return redirect('appointments:appointment_list')

        if not appointment.can_cancel():
            messages.error(request, 'This appointment cannot be cancelled. It may be too close to the appointment time.')
            return redirect('appointments:appointment_detail', pk=pk)

    elif request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    form = AppointmentCancelForm(request.POST or None)

    if request.method == 'POST':
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('appointments:appointment_list')

    return render(request, 'appointments/cancel_appointment.html', {
        'appointment': appointment,
        'form': form
    })


# ─── MARK AS COMPLETED ───────────────────────────────────────────────────────

@login_required
def complete_appointment(request, pk):
    """Doctor marks appointment as completed."""
    if request.user.role not in ['DOCTOR', 'ADMIN', 'RECEPTIONIST']:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    appointment = get_object_or_404(Appointment, pk=pk)

    if request.user.role == 'DOCTOR':
        if appointment.doctor != request.user.doctor_profile:
            messages.error(request, 'Access denied.')
            return redirect('appointments:appointment_list')

    if request.method == 'POST':
        appointment.status = 'COMPLETED'
        appointment.save()
        messages.success(request, 'Appointment marked as completed.')
        return redirect('appointments:appointment_list')

    return render(request, 'appointments/complete_appointment.html', {
        'appointment': appointment
    })


# ─── DOWNLOAD PDF ────────────────────────────────────────────────────────────

@login_required
def download_pdf(request, pk):
    """Download appointment PDF slip."""
    appointment = get_object_or_404(Appointment, pk=pk)

    # Security check
    if request.user.role == 'PATIENT':
        if appointment.patient != request.user.patient_profile:
            messages.error(request, 'Access denied.')
            return redirect('appointments:appointment_list')

    if appointment.pdf_file:
        response = FileResponse(
            appointment.pdf_file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="appointment_{appointment.id}.pdf"'
        return response
    else:
        # Regenerate PDF if missing
        generate_qr_code(appointment)
        generate_appointment_pdf(appointment)
        appointment.save()

        if appointment.pdf_file:
            response = FileResponse(
                appointment.pdf_file.open('rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="appointment_{appointment.id}.pdf"'
            return response

        messages.error(request, 'PDF not available. Please try again.')
        return redirect('appointments:appointment_detail', pk=pk)


# ─── API: GET AVAILABLE SLOTS (JSON) ─────────────────────────────────────────

@login_required
def get_slots_api(request):
    """API endpoint to get available slots for a doctor on a date."""
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'error': 'Missing doctor_id or date'}, status=400)

    try:
        doctor = Doctor.objects.get(id=doctor_id)
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        slots = generate_available_slots(doctor, booking_date)
        return JsonResponse({'slots': slots})
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)


# ─── TODAY'S APPOINTMENTS (Doctor Dashboard) ─────────────────────────────────

@login_required
def todays_appointments(request):
    """Doctor views today's appointments."""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    today = date.today()
    appointments = Appointment.objects.filter(
        doctor=request.user.doctor_profile,
        date=today,
        status__in=['PENDING', 'CONFIRMED']
    ).select_related('patient').order_by('start_time')

    return render(request, 'appointments/todays_appointments.html', {
        'appointments': appointments,
        'today': today
    })


# ─── WAITING LIST ─────────────────────────────────────────────────────────────

@login_required
def join_waiting_list(request, doctor_id, date_str):
    """Patient joins waiting list for a fully booked doctor."""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    doctor = get_object_or_404(Doctor, id=doctor_id)
    try:
        waiting_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Invalid date.')
        return redirect('appointments:book_step1')

    patient = request.user.patient_profile

    # Check if already in waiting list
    already_waiting = WaitingList.objects.filter(
        patient=patient,
        doctor=doctor,
        date=waiting_date
    ).exists()

    if already_waiting:
        messages.info(request, 'You are already on the waiting list for this date.')
    else:
        WaitingList.objects.create(
            patient=patient,
            doctor=doctor,
            date=waiting_date
        )
        messages.success(request, 'Added to waiting list! We will notify you if a slot opens up.')

    return redirect('appointments:appointment_list')