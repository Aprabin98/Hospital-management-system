"""
Lab Result Workflow Views
Handles result status transitions: PENDING → ENTERED → REVIEWED → APPROVED → RELEASED
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Count

from .models import TestResult, TestResultItem, TestBooking
from notifications.utils import create_notification


# ===============================================
# LAB TECHNICIAN WORKFLOW
# ===============================================

@login_required
def lab_result_entry_queue(request):
    """Lab technician views samples ready for result entry"""
    if request.user.role != 'LAB_TECHNICIAN':
        messages.error(request, 'Access denied. Lab technicians only.')
        return redirect('users:dashboard')
    
    # Bookings with samples collected, waiting for results
    pending_results = TestBooking.objects.filter(
        status='SAMPLE_COLLECTED'
    ).select_related('patient__user', 'template').order_by('date')
    
    # Bookings where results were already entered
    completed_results = TestResult.objects.filter(
        status='ENTERED'
    ).select_related('booking__patient__user', 'booking__template', 'filled_by').order_by('-filled_at')[:20]
    
    context = {
        'pending_results_count': pending_results.count(),
        'pending_results': pending_results[:50],
        'completed_results': completed_results,
    }
    return render(request, 'lab/workflow/entry_queue.html', context)


@login_required
def lab_result_mark_entered(request, booking_id):
    """After entering results, mark status as ENTERED (not PROCESSING)"""
    if request.user.role != 'LAB_TECHNICIAN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    booking = get_object_or_404(TestBooking, id=booking_id)
    result = get_object_or_404(TestResult, booking=booking)
    
    with transaction.atomic():
        result.status = 'ENTERED'
        result.save(update_fields=['status'])
        
        messages.success(request, f'Results marked as entered for {booking.patient.full_name}')
    
    return redirect('lab:lab_result_entry_queue')


# ===============================================
# DOCTOR WORKFLOW - RESULT REVIEW & APPROVAL
# ===============================================

@login_required
def doctor_awaiting_review(request):
    """Doctor views lab results awaiting review"""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied. Doctors only.')
        return redirect('users:dashboard')
    
    doctor = request.user.doctor_profile
    
    # Get results for doctor's patients
    from appointments.models import Appointment
    patient_ids = Appointment.objects.filter(
        doctor=doctor
    ).values_list('patient_id', flat=True).distinct()
    
    # Results in ENTERED status (awaiting doctor review)
    pending_review = TestResult.objects.filter(
        status='ENTERED',
        booking__patient_id__in=patient_ids
    ).select_related('booking__patient__user', 'booking__template', 'filled_by').order_by('-filled_at')
    
    # Critical results (flagged as having critical values)
    critical_results = TestResult.objects.filter(
        status__in=['ENTERED', 'REVIEWED'],
        has_critical_values=True,
        booking__patient_id__in=patient_ids
    ).select_related('booking__patient__user', 'booking__template').order_by('-filled_at')
    
    # Already reviewed/approved
    reviewed_results = TestResult.objects.filter(
        status__in=['REVIEWED', 'APPROVED'],
        reviewed_by=doctor
    ).select_related('booking__patient__user', 'booking__template').order_by('-reviewed_at')[:20]
    
    context = {
        'pending_review': pending_review,
        'critical_results': critical_results,
        'reviewed_results': reviewed_results,
        'doctor': doctor,
    }
    return render(request, 'lab/workflow/doctor_review.html', context)


@login_required
def doctor_review_result(request, result_id):
    """Doctor reviews and approves a lab result"""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    doctor = request.user.doctor_profile
    result = get_object_or_404(TestResult, id=result_id)
    
    # Verify doctor has access (is treating this patient)
    from appointments.models import Appointment
    can_review = Appointment.objects.filter(
        doctor=doctor,
        patient=result.booking.patient
    ).exists()
    
    if not can_review:
        messages.error(request, 'You can only review results for your patients.')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        doctor_notes = request.POST.get('doctor_notes', '').strip()
        
        with transaction.atomic():
            if action == 'approve':
                result.status = 'APPROVED'
                result.reviewed_by = doctor
                result.reviewed_at = timezone.now()
                result.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
                
                # Notify patient
                patient = result.booking.patient
                if patient.user:
                    create_notification(
                        recipient=patient.user,
                        title='Lab Results Approved',
                        message=f'Your {result.booking.template.name} lab results have been reviewed and approved.',
                        notification_type='LAB',
                    )
                
                messages.success(request, 'Results approved and patient notified.')
                
            elif action == 'needs_retest':
                result.status = 'ENTERED'
                result.notes = f"{result.notes}\n[Doctor: Retest needed - {doctor_notes}]"
                result.save(update_fields=['notes', 'status'])
                
                messages.warning(request, 'Result flagged for retest.')
        
        return redirect('doctor:awaiting_review')
    
    # GET - Show review form
    items = result.items.select_related('field').order_by('field__order')
    critical_items = items.filter(is_critical=True)
    
    context = {
        'result': result,
        'booking': result.booking,
        'items': items,
        'critical_items': critical_items,
        'doctor': doctor,
    }
    return render(request, 'lab/workflow/doctor_review_form.html', context)


@login_required
def doctor_critical_results_dashboard(request):
    """Doctor views all critical lab results for their patients"""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    doctor = request.user.doctor_profile
    
    from appointments.models import Appointment
    patient_ids = Appointment.objects.filter(
        doctor=doctor
    ).values_list('patient_id', flat=True).distinct()
    
    # Get all results with critical values for this doctor's patients
    critical_results = TestResult.objects.filter(
        has_critical_values=True,
        booking__patient_id__in=patient_ids
    ).select_related(
        'booking__patient__user',
        'booking__template',
        'reviewed_by'
    ).prefetch_related('items__field').order_by('-filled_at')
    
    context = {
        'critical_results': critical_results,
        'total_critical': critical_results.count(),
        'reviewed_critical': critical_results.filter(reviewed_by=doctor).count(),
    }
    return render(request, 'lab/workflow/critical_dashboard.html', context)


# ===============================================
# ADMIN WORKFLOW - RESULT RELEASE
# ===============================================

@login_required
def admin_results_to_release(request):
    """Admin views results approved and ready to release to patients"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admins only.')
        return redirect('users:dashboard')
    
    # Results approved but not yet released
    approved_results = TestResult.objects.filter(
        status='APPROVED',
        is_released=False
    ).select_related(
        'booking__patient__user',
        'booking__template',
        'reviewed_by'
    ).order_by('-reviewed_at')
    
    # Already released results (past week)
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    released_results = TestResult.objects.filter(
        status='RELEASED',
        released_at__gte=week_ago
    ).select_related('booking__patient__user', 'booking__template').order_by('-released_at')[:50]
    
    context = {
        'approved_results': approved_results,
        'released_results': released_results,
    }
    return render(request, 'lab/workflow/admin_release.html', context)


@login_required
def admin_release_result(request, result_id):
    """Admin releases result to patient"""
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    result = get_object_or_404(TestResult, id=result_id, status='APPROVED')
    
    if request.method == 'POST':
        with transaction.atomic():
            result.status = 'RELEASED'
            result.is_released = True
            result.released_at = timezone.now()
            result.save(update_fields=['status', 'is_released', 'released_at'])
            
            # Notify patient
            patient = result.booking.patient
            if patient.user:
                create_notification(
                    recipient=patient.user,
                    title='Lab Results Available',
                    message=f'Your {result.booking.template.name} lab results are now available. You can view them in your health records.',
                    notification_type='LAB',
                )
            
            messages.success(request, f'Released to {patient.full_name}')
        
        return redirect('lab:admin_results_to_release')
    
    return JsonResponse({'error': 'POST required'}, status=400)


# ===============================================
# PATIENT WORKFLOW - VIEW RESULTS
# ===============================================

@login_required
def patient_lab_results(request):
    """Patient views all their released lab results"""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    patient = request.user.patient_profile
    
    # Released results
    released_results = TestResult.objects.filter(
        status='RELEASED',
        booking__patient=patient
    ).select_related('booking__patient__user', 'booking__template', 'reviewed_by').order_by('-released_at')
    
    # Pending (approved but not released yet)
    pending_release = TestResult.objects.filter(
        status='APPROVED',
        booking__patient=patient
    ).select_related('booking__template', 'reviewed_by').order_by('-reviewed_at')
    
    context = {
        'released_results': released_results,
        'pending_release': pending_release,
    }
    return render(request, 'lab/workflow/patient_results.html', context)


@login_required
def patient_view_result_detail(request, result_id):
    """Patient views detailed lab result"""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    
    patient = request.user.patient_profile
    result = get_object_or_404(TestResult, id=result_id, booking__patient=patient, status='RELEASED')
    
    items = result.items.select_related('field').order_by('field__order')
    
    context = {
        'result': result,
        'booking': result.booking,
        'items': items,
        'template': result.booking.template,
    }
    return render(request, 'lab/workflow/patient_result_detail.html', context)


# ===============================================
# API ENDPOINTS - RESULT WORKFLOW STATUS
# ===============================================

@login_required
def api_result_workflow_status(request, result_id):
    """API endpoint to get current result workflow status"""
    result = get_object_or_404(TestResult, id=result_id)
    
    # Check access permissions
    user = request.user
    if user.role == 'PATIENT':
        if result.booking.patient.user != user or result.status != 'RELEASED':
            return JsonResponse({'error': 'Access denied'}, status=403)
    elif user.role == 'DOCTOR':
        from appointments.models import Appointment
        can_view = Appointment.objects.filter(
            doctor=user.doctor_profile,
            patient=result.booking.patient
        ).exists()
        if not can_view:
            return JsonResponse({'error': 'Access denied'}, status=403)
    elif user.role not in ['ADMIN', 'LAB_TECHNICIAN']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    data = {
        'result_id': result.id,
        'status': result.status,
        'status_display': result.get_status_display(),
        'booking': {
            'id': result.booking.id,
            'patient_name': result.booking.patient.full_name,
            'test_name': result.booking.template.name,
            'specimen_id': result.booking.specimen_id,
        },
        'timeline': {
            'filled_at': result.filled_at.isoformat() if result.filled_at else None,
            'reviewed_at': result.reviewed_at.isoformat() if result.reviewed_at else None,
            'released_at': result.released_at.isoformat() if result.released_at else None,
        },
        'critical_values': result.has_critical_values,
        'critical_notification_sent': result.critical_notification_sent,
    }
    return JsonResponse(data)


@login_required
def api_result_workflow_stats(request):
    """API endpoint for lab workflow statistics"""
    if request.user.role not in ['ADMIN', 'DOCTOR', 'LAB_TECHNICIAN']:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    stats = {
        'total_pending_entry': TestBooking.objects.filter(status='SAMPLE_COLLECTED').count(),
        'total_awaiting_review': TestResult.objects.filter(status='ENTERED').count(),
        'total_awaiting_release': TestResult.objects.filter(status='APPROVED').count(),
        'total_released': TestResult.objects.filter(status='RELEASED').count(),
        'critical_results_pending': TestResult.objects.filter(
            has_critical_values=True,
            status__in=['ENTERED', 'REVIEWED']
        ).count(),
        'results_by_status': dict(
            TestResult.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        ),
    }
    return JsonResponse(stats)
