from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from django.utils import timezone
from datetime import datetime, time, timedelta

from .models import TestTemplate, TestField, TestSchedule, TestBooking, TestResult, TestResultItem
from .forms import TestTemplateForm, TestFieldForm, TestScheduleForm, TestBookingForm, TestResultForm
from .api_serializers import TestTemplateSerializer
from .utils import generate_lab_report_pdf
from notifications.utils import create_notification
from appointments.models import Appointment


def _doctor_can_view_patient_reports(doctor, patient):
    return Appointment.objects.filter(
        doctor=doctor,
        patient=patient,
        status__in=['CONFIRMED', 'COMPLETED']
    ).exists()


def _notify_critical_results(result):
    critical_items = result.items.filter(is_critical=True).select_related('field')
    if not critical_items.exists():
        return

    fields = ', '.join(item.field.field_name for item in critical_items[:3])
    if critical_items.count() > 3:
        fields += ', ...'

    patient_user = result.booking.patient.user
    message = (
        f"Critical lab values detected for {result.booking.template.name}: {fields}. "
        f"Please contact hospital staff immediately."
    )

    create_notification(
        recipient=patient_user,
        title='Critical Lab Alert',
        message=message,
        notification_type='LAB',
    )

    latest_appointment = Appointment.objects.filter(
        patient=result.booking.patient,
        status__in=['CONFIRMED', 'COMPLETED']
    ).select_related('doctor__user').order_by('-date', '-start_time').first()

    recipients = {patient_user.id}
    if latest_appointment and latest_appointment.doctor.user_id not in recipients:
        recipients.add(latest_appointment.doctor.user_id)
        create_notification(
            recipient=latest_appointment.doctor.user,
            title='Critical Lab Alert',
            message=f"Critical lab values detected for patient {result.booking.patient.full_name}: {fields}.",
            notification_type='LAB',
        )


def _allowed_next_status(current_status):
    transitions = {
        'PENDING': ['SAMPLE_COLLECTED', 'CANCELLED', 'REJECTED_SAMPLE'],
        'SAMPLE_COLLECTED': ['PROCESSING', 'REJECTED_SAMPLE'],
        'PROCESSING': ['COMPLETED'],
        'COMPLETED': [],
        'REJECTED_SAMPLE': [],
        'CANCELLED': [],
    }
    return transitions.get(current_status, [])


# ─── ADMIN: TEST TEMPLATE MANAGEMENT ─────────────────────────────────────────

@login_required
def template_list(request):
    """Admin views all test templates."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    templates = TestTemplate.objects.all()
    return render(request, 'lab/template_list.html', {'templates': templates})


@login_required
def template_create(request):
    """Admin creates a new test template."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    form = TestTemplateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        template = form.save()
        messages.success(request, f'{template.name} created! Now add test fields.')
        return redirect('lab:template_fields', pk=template.pk)

    return render(request, 'lab/template_form.html', {'form': form, 'title': 'Create Test Template'})


@login_required
def template_edit(request, pk):
    """Admin edits a test template."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    template = get_object_or_404(TestTemplate, pk=pk)
    form = TestTemplateForm(request.POST or None, instance=template)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Template updated!')
        return redirect('lab:template_list')

    return render(request, 'lab/template_form.html', {'form': form, 'title': 'Edit Template', 'template': template})


@login_required
def template_delete(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    template = get_object_or_404(TestTemplate, pk=pk)
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Template deleted!')
        return redirect('lab:template_list')

    return render(request, 'lab/template_confirm_delete.html', {'template': template})


# ─── ADMIN: TEST FIELDS ───────────────────────────────────────────────────────

@login_required
def template_fields(request, pk):
    """Admin manages fields for a test template."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    template = get_object_or_404(TestTemplate, pk=pk)
    fields = template.fields.all()
    form = TestFieldForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        field = form.save(commit=False)
        field.template = template
        field.save()
        messages.success(request, 'Field added!')
        return redirect('lab:template_fields', pk=pk)

    return render(request, 'lab/template_fields.html', {
        'template': template,
        'fields': fields,
        'form': form
    })


@login_required
def field_delete(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    field = get_object_or_404(TestField, pk=pk)
    template_pk = field.template.pk
    if request.method == 'POST':
        field.delete()
        messages.success(request, 'Field deleted!')
    return redirect('lab:template_fields', pk=template_pk)


# ─── ADMIN: TEST SCHEDULES ────────────────────────────────────────────────────

@login_required
def template_schedule(request, pk):
    """Admin manages schedule for a test template."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    template = get_object_or_404(TestTemplate, pk=pk)
    schedules = template.schedules.all()
    form = TestScheduleForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        schedule = form.save(commit=False)
        schedule.template = template
        try:
            schedule.save()
            messages.success(request, 'Schedule added!')
        except Exception:
            messages.error(request, 'Schedule already exists for this day.')
        return redirect('lab:template_schedule', pk=pk)

    return render(request, 'lab/template_schedule.html', {
        'template': template,
        'schedules': schedules,
        'form': form
    })


@login_required
def schedule_delete(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    schedule = get_object_or_404(TestSchedule, pk=pk)
    template_pk = schedule.template.pk
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted!')
    return redirect('lab:template_schedule', pk=template_pk)


# ─── PATIENT: BROWSE & BOOK TESTS ────────────────────────────────────────────

@login_required
def test_list(request):
    """Patient browses available tests."""
    if request.user.role not in ['PATIENT', 'RECEPTIONIST']:
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    templates = list(TestTemplate.objects.filter(is_available=True).prefetch_related('schedules'))
    for template in templates:
        template.available_dates = TestTemplateSerializer(template).data['available_dates']
    return render(request, 'lab/test_list.html', {'templates': templates})


@login_required
def test_detail(request, pk):
    """Patient views test details before booking."""
    template = get_object_or_404(TestTemplate, pk=pk, is_available=True)
    fields = template.fields.all()
    schedules = template.schedules.filter(is_active=True)
    available_dates = TestTemplateSerializer(template).data['available_dates']

    return render(request, 'lab/test_detail.html', {
        'template': template,
        'fields': fields,
        'schedules': schedules,
        'available_dates': available_dates,
    })


@login_required
def book_test(request, pk):
    """Patient books a lab test."""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    template = get_object_or_404(TestTemplate, pk=pk, is_available=True)
    form = TestBookingForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        date = form.cleaned_data['date']
        patient = request.user.patient_profile

        # Check same test same date rule
        already_booked = TestBooking.objects.filter(
            patient=patient,
            template=template,
            date=date,
            status__in=['PENDING', 'SAMPLE_COLLECTED', 'PROCESSING']
        ).exists()

        if already_booked:
            messages.error(request, f'You already have a {template.name} booking on this date!')
            return redirect('lab:book_test', pk=pk)

        # Check max bookings per day
        day_name = date.strftime('%A')[:3].upper()
        try:
            schedule = TestSchedule.objects.get(
                template=template,
                day=day_name,
                is_active=True
            )
            day_bookings = TestBooking.objects.filter(
                template=template,
                date=date,
                status__in=['PENDING', 'SAMPLE_COLLECTED', 'PROCESSING']
            ).count()

            if day_bookings >= schedule.max_bookings:
                messages.error(request, 'Sorry, this test is fully booked for this date.')
                return redirect('lab:book_test', pk=pk)

        except TestSchedule.DoesNotExist:
            messages.error(request, 'This test is not available on the selected day.')
            return redirect('lab:book_test', pk=pk)

        # Create booking
        booking = form.save(commit=False)
        booking.patient = patient
        booking.template = template
        booking.amount = template.price
        booking.expected_report_at = timezone.make_aware(
            datetime.combine(date, time(18, 0))
        ) + timedelta(minutes=template.duration_minutes)
        booking.save()

        messages.success(request, f'{template.name} booked successfully for {date}!')
        return redirect('lab:my_bookings')

    return render(request, 'lab/book_test.html', {
        'template': template,
        'form': form,
    })


# ─── PATIENT: MY BOOKINGS ────────────────────────────────────────────────────

@login_required
def my_bookings(request):
    """Patient views their test bookings."""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    bookings = TestBooking.objects.filter(
        patient=request.user.patient_profile
    ).select_related('template').order_by('-date')

    return render(request, 'lab/my_bookings.html', {'bookings': bookings})


@login_required
def booking_detail(request, pk):
    """View booking details and result if available."""
    booking = get_object_or_404(TestBooking, pk=pk)

    # Security
    if request.user.role == 'PATIENT':
        if booking.patient != request.user.patient_profile:
            messages.error(request, 'Access denied.')
            return redirect('lab:my_bookings')

    result = None
    try:
        if booking.result.is_released or request.user.role in ['ADMIN', 'LAB_TECHNICIAN']:
            result = booking.result
    except TestResult.DoesNotExist:
        pass

    return render(request, 'lab/booking_detail.html', {
        'booking': booking,
        'result': result,
    })


@login_required
def cancel_booking(request, pk):
    """Patient cancels a test booking."""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    booking = get_object_or_404(
        TestBooking,
        pk=pk,
        patient=request.user.patient_profile
    )

    if booking.status != 'PENDING':
        messages.error(request, 'Only pending bookings can be cancelled.')
        return redirect('lab:my_bookings')

    if request.method == 'POST':
        booking.status = 'CANCELLED'
        booking.save()
        messages.success(request, 'Booking cancelled successfully.')
        return redirect('lab:my_bookings')

    return render(request, 'lab/cancel_booking.html', {'booking': booking})


# ─── LAB TECHNICIAN: FILL RESULTS ────────────────────────────────────────────

@login_required
def lab_dashboard(request):
    """Lab technician dashboard."""
    if request.user.role != 'LAB_TECHNICIAN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    from datetime import date
    today = date.today()

    pending_bookings = TestBooking.objects.filter(
        status__in=['PENDING', 'SAMPLE_COLLECTED', 'PROCESSING'],
    ).select_related('patient', 'template').order_by('date')

    todays_bookings = pending_bookings.filter(date=today)
    overdue_bookings = pending_bookings.filter(expected_report_at__lt=timezone.now())

    return render(request, 'lab/lab_dashboard.html', {
        'pending_bookings': pending_bookings,
        'todays_bookings': todays_bookings,
        'overdue_bookings': overdue_bookings,
        'today': today,
    })


@login_required
def fill_result(request, booking_id):
    """Lab technician fills test results."""
    if request.user.role != 'LAB_TECHNICIAN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    booking = get_object_or_404(TestBooking, pk=booking_id)
    fields = booking.template.fields.all().order_by('order')

    # Check if result already exists
    try:
        existing_result = booking.result
        messages.info(request, 'Result already exists. You can update it.')
        return redirect('lab:update_result', pk=existing_result.pk)
    except TestResult.DoesNotExist:
        pass

    if request.method == 'POST':
        result_form = TestResultForm(request.POST)

        if result_form.is_valid():
            # Create result
            result = TestResult.objects.create(
                booking=booking,
                filled_by=request.user,
                notes=result_form.cleaned_data['notes'],
            )

            # Save each field value
            for field in fields:
                value = request.POST.get(f'field_{field.id}', '').strip()
                item = TestResultItem(
                    result=result,
                    field=field,
                    value=value if value else None,
                )
                item.save()  # auto calculates status

            # Update booking status
            booking.status = 'PROCESSING'
            booking.save()

            # Generate PDF
            generate_lab_report_pdf(result)
            result.save()

            _notify_critical_results(result)

            messages.success(request, 'Results saved successfully!')
            return redirect('lab:lab_dashboard')

    else:
        result_form = TestResultForm()

    return render(request, 'lab/fill_result.html', {
        'booking': booking,
        'fields': fields,
        'result_form': result_form,
    })


@login_required
def update_result(request, pk):
    """Lab technician updates existing result."""
    if request.user.role != 'LAB_TECHNICIAN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    result = get_object_or_404(TestResult, pk=pk)
    booking = result.booking
    fields = booking.template.fields.all().order_by('order')
    existing_items = {item.field.id: item for item in result.items.all()}

    if request.method == 'POST':
        result_form = TestResultForm(request.POST, instance=result)

        if result_form.is_valid():
            result_form.save()

            # Update field values
            for field in fields:
                value = request.POST.get(f'field_{field.id}', '').strip()
                if field.id in existing_items:
                    item = existing_items[field.id]
                    item.value = value if value else None
                    item.save()
                else:
                    TestResultItem.objects.create(
                        result=result,
                        field=field,
                        value=value if value else None,
                    )

            # Regenerate PDF
            generate_lab_report_pdf(result)
            result.save()

            _notify_critical_results(result)

            messages.success(request, 'Results updated!')
            return redirect('lab:lab_dashboard')

    else:
        result_form = TestResultForm(instance=result)

    return render(request, 'lab/update_result.html', {
        'result': result,
        'booking': booking,
        'fields': fields,
        'existing_items': existing_items,
        'result_form': result_form,
    })


# ─── ADMIN: RELEASE RESULT ────────────────────────────────────────────────────

@login_required
def admin_bookings(request):
    """Admin views all test bookings."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    bookings = TestBooking.objects.all().select_related(
        'patient', 'template'
    ).order_by('-date')

    return render(request, 'lab/admin_bookings.html', {'bookings': bookings})


@login_required
def release_result(request, pk):
    """Admin releases result to patient."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    result = get_object_or_404(TestResult, pk=pk)

    if request.method == 'POST':
        if not result.is_verified:
            messages.error(request, 'Please verify this report before release.')
            return redirect('lab:admin_bookings')

        if result.booking.payment_status != 'PAID':
            messages.error(request, 'Cannot release report before lab payment is marked paid.')
            return redirect('lab:admin_bookings')

        result.is_released = True
        result.released_at = timezone.now()
        result.booking.status = 'COMPLETED'
        result.booking.completed_at = timezone.now()
        result.booking.save(update_fields=['status', 'completed_at'])
        result.save()
        messages.success(request, 'Report released to patient!')
        return redirect('lab:admin_bookings')

    return render(request, 'lab/release_confirm.html', {'result': result})


@login_required
def verify_result(request, pk):
    """Admin verifies result before releasing report."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    result = get_object_or_404(TestResult, pk=pk)

    if request.method == 'POST':
        result.is_verified = True
        result.verified_by = request.user
        result.verified_at = timezone.now()
        result.save(update_fields=['is_verified', 'verified_by', 'verified_at'])
        messages.success(request, 'Report verified. You can now release it to patient.')
        return redirect('lab:admin_bookings')

    return render(request, 'lab/release_confirm.html', {'result': result, 'verify_mode': True})


# ─── DOWNLOAD REPORT ─────────────────────────────────────────────────────────

@login_required
def download_report(request, pk):
    """Download lab report PDF."""
    result = get_object_or_404(TestResult, pk=pk)

    # Security
    if request.user.role == 'PATIENT':
        if result.booking.patient != request.user.patient_profile:
            messages.error(request, 'Access denied.')
            return redirect('lab:my_bookings')
        if not result.is_released:
            messages.error(request, 'Report not released yet.')
            return redirect('lab:my_bookings')

    if not result.pdf_file:
        generate_lab_report_pdf(result)
        result.save()

    if result.pdf_file:
        response = FileResponse(
            result.pdf_file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="lab_report_{result.id}.pdf"'
        return response

    messages.error(request, 'Report not available.')
    return redirect('lab:my_bookings')



# ─── UPDATE BOOKING STATUS (Lab Technician) ──────────────────────────────────

@login_required
def update_booking_status(request, pk):
    """Lab technician updates booking status manually."""
    if request.user.role != 'LAB_TECHNICIAN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    booking = get_object_or_404(TestBooking, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        rejected_reason = request.POST.get('rejected_reason', '').strip()

        allowed = _allowed_next_status(booking.status)
        if new_status not in allowed:
            messages.error(request, f'Invalid status transition: {booking.get_status_display()} -> {new_status}.')
            return redirect('lab:lab_dashboard')

        if new_status == 'SAMPLE_COLLECTED':
            booking.collected_by = request.user
            booking.collected_at = timezone.now()
            if not booking.specimen_id:
                booking.specimen_id = f"SP-{booking.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        elif new_status == 'PROCESSING':
            booking.received_at = booking.received_at or timezone.now()
        elif new_status == 'REJECTED_SAMPLE':
            if not rejected_reason:
                messages.error(request, 'Please provide a rejected sample reason.')
                return redirect('lab:lab_dashboard')
            booking.rejected_reason = rejected_reason

        booking.status = new_status
        booking.save()
        messages.success(request, f'Status updated to {booking.get_status_display()}!')

    return redirect('lab:lab_dashboard')


# ─── DOCTOR: VIEW PATIENT LAB REPORTS ────────────────────────────────────────

@login_required
def patient_reports_for_doctor(request, patient_id):
    """Doctor views a patient's completed lab reports."""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    from users.models import PatientProfile
    patient = get_object_or_404(PatientProfile, pk=patient_id)

    if not _doctor_can_view_patient_reports(request.user.doctor_profile, patient):
        messages.error(request, 'Access denied. You can only view reports of your own patients.')
        return redirect('users:dashboard')

    bookings = TestBooking.objects.filter(
        patient=patient,
        status='COMPLETED'
    ).select_related('template').order_by('-date')

    return render(request, 'lab/patient_reports.html', {
        'patient': patient,
        'bookings': bookings,
    })