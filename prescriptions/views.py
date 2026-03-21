from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse

from .models import Prescription, PrescriptionItem
from .forms import PrescriptionForm, PrescriptionItemFormSet
from .utils import generate_prescription_pdf
from appointments.models import Appointment


# ─── WRITE PRESCRIPTION (Doctor) ─────────────────────────────────────────────

@login_required
def write_prescription(request, appointment_id):
    """Doctor writes prescription for a completed appointment."""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied. Doctors only.')
        return redirect('users:dashboard')

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=request.user.doctor_profile
    )

    # Only for completed appointments
    if appointment.status != 'COMPLETED':
        messages.error(request, 'You can only write prescriptions for completed appointments.')
        return redirect('appointments:appointment_detail', pk=appointment_id)

    # Check if prescription already exists
    existing = Prescription.objects.filter(appointment=appointment).first()
    if existing:
        messages.info(request, 'Prescription already exists. You can edit it.')
        return redirect('prescriptions:edit_prescription', pk=existing.id)

    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        formset = PrescriptionItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            # Save prescription
            prescription = form.save(commit=False)
            prescription.appointment = appointment
            prescription.doctor = request.user.doctor_profile
            prescription.patient = appointment.patient
            prescription.save()

            # Save medicines
            formset.instance = prescription
            formset.save()

            # Generate PDF
            generate_prescription_pdf(prescription)
            prescription.save()

            messages.success(request, 'Prescription written successfully!')
            return redirect('prescriptions:prescription_detail', pk=prescription.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = PrescriptionForm()
        formset = PrescriptionItemFormSet()

    return render(request, 'prescriptions/write_prescription.html', {
        'form': form,
        'formset': formset,
        'appointment': appointment,
    })


# ─── EDIT PRESCRIPTION (Doctor) ──────────────────────────────────────────────

@login_required
def edit_prescription(request, pk):
    """Doctor edits existing prescription."""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    prescription = get_object_or_404(
        Prescription,
        pk=pk,
        doctor=request.user.doctor_profile
    )

    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription)
        formset = PrescriptionItemFormSet(request.POST, instance=prescription)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()

            # Regenerate PDF
            generate_prescription_pdf(prescription)
            prescription.save()

            messages.success(request, 'Prescription updated successfully!')
            return redirect('prescriptions:prescription_detail', pk=prescription.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = PrescriptionForm(instance=prescription)
        formset = PrescriptionItemFormSet(instance=prescription)

    return render(request, 'prescriptions/edit_prescription.html', {
        'form': form,
        'formset': formset,
        'prescription': prescription,
    })


# ─── VIEW PRESCRIPTION ───────────────────────────────────────────────────────

@login_required
def prescription_detail(request, pk):
    """View prescription details."""
    prescription = get_object_or_404(Prescription, pk=pk)

    # Security - only doctor who wrote it or patient it belongs to
    if request.user.role == 'PATIENT':
        if prescription.patient != request.user.patient_profile:
            messages.error(request, 'Access denied.')
            return redirect('prescriptions:patient_prescriptions')

    elif request.user.role == 'DOCTOR':
        if prescription.doctor != request.user.doctor_profile:
            messages.error(request, 'Access denied.')
            return redirect('prescriptions:doctor_prescriptions')

    return render(request, 'prescriptions/prescription_detail.html', {
        'prescription': prescription,
        'items': prescription.items.all(),
    })


# ─── PATIENT: MY PRESCRIPTIONS ───────────────────────────────────────────────

@login_required
def patient_prescriptions(request):
    """Patient views all their prescriptions."""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    prescriptions = Prescription.objects.filter(
        patient=request.user.patient_profile
    ).select_related(
        'doctor__user', 'doctor__specialization', 'appointment'
    ).order_by('-created_at')

    return render(request, 'prescriptions/patient_prescriptions.html', {
        'prescriptions': prescriptions
    })


# ─── DOCTOR: MY PRESCRIPTIONS ────────────────────────────────────────────────

@login_required
def doctor_prescriptions(request):
    """Doctor views all prescriptions they wrote."""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    prescriptions = Prescription.objects.filter(
        doctor=request.user.doctor_profile
    ).select_related(
        'patient', 'appointment'
    ).order_by('-created_at')

    return render(request, 'prescriptions/doctor_prescriptions.html', {
        'prescriptions': prescriptions
    })


# ─── DOWNLOAD PRESCRIPTION PDF ───────────────────────────────────────────────

@login_required
def download_prescription_pdf(request, pk):
    """Download prescription PDF."""
    prescription = get_object_or_404(Prescription, pk=pk)

    # Security check
    if request.user.role == 'PATIENT':
        if prescription.patient != request.user.patient_profile:
            messages.error(request, 'Access denied.')
            return redirect('prescriptions:patient_prescriptions')

    elif request.user.role == 'DOCTOR':
        if prescription.doctor != request.user.doctor_profile:
            messages.error(request, 'Access denied.')
            return redirect('prescriptions:doctor_prescriptions')

    # Regenerate if missing
    if not prescription.pdf_file:
        generate_prescription_pdf(prescription)
        prescription.save()

    if prescription.pdf_file:
        response = FileResponse(
            prescription.pdf_file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.id}.pdf"'
        return response

    messages.error(request, 'PDF not available. Please try again.')
    return redirect('prescriptions:prescription_detail', pk=pk)