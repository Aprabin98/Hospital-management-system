from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q

from .models import Specialization, Doctor, Shift, DoctorSchedule, DoctorLeave
from .forms import (
    DoctorCreationForm, DoctorEditForm, SpecializationForm,
    ShiftForm, DoctorScheduleForm, DoctorLeaveForm, DoctorSearchForm
)


# ─── DECORATOR HELPERS ───────────────────────────────────────────────────────

def admin_required(view_func):
    """Only ADMIN can access."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            messages.error(request, 'Access denied. Admins only.')
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_or_receptionist_required(view_func):
    """ADMIN or RECEPTIONIST can access."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
            messages.error(request, 'Access denied.')
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── SPECIALIZATION VIEWS ────────────────────────────────────────────────────

@login_required
def specialization_list(request):
    """Admin manages specializations."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    specializations = Specialization.objects.all()
    form = SpecializationForm()

    if request.method == 'POST':
        form = SpecializationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Specialization added successfully!')
            return redirect('clinical:specialization_list')

    return render(request, 'clinical/specialization_list.html', {
        'specializations': specializations,
        'form': form
    })


@login_required
def specialization_edit(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    specialization = get_object_or_404(Specialization, pk=pk)
    form = SpecializationForm(request.POST or None, instance=specialization)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Specialization updated!')
        return redirect('clinical:specialization_list')

    return render(request, 'clinical/specialization_edit.html', {'form': form, 'specialization': specialization})


@login_required
def specialization_delete(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    specialization = get_object_or_404(Specialization, pk=pk)
    if request.method == 'POST':
        specialization.delete()
        messages.success(request, 'Specialization deleted!')
        return redirect('clinical:specialization_list')

    return render(request, 'clinical/specialization_confirm_delete.html', {'specialization': specialization})


# ─── SHIFT VIEWS ─────────────────────────────────────────────────────────────

@login_required
def shift_list(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    shifts = Shift.objects.all()
    form = ShiftForm()

    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shift added successfully!')
            return redirect('clinical:shift_list')

    return render(request, 'clinical/shift_list.html', {'shifts': shifts, 'form': form})


@login_required
def shift_edit(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    shift = get_object_or_404(Shift, pk=pk)
    form = ShiftForm(request.POST or None, instance=shift)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Shift updated!')
        return redirect('clinical:shift_list')

    return render(request, 'clinical/shift_edit.html', {'form': form, 'shift': shift})


@login_required
def shift_delete(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    shift = get_object_or_404(Shift, pk=pk)
    if request.method == 'POST':
        shift.delete()
        messages.success(request, 'Shift deleted!')
        return redirect('clinical:shift_list')

    return render(request, 'clinical/shift_confirm_delete.html', {'shift': shift})


# ─── DOCTOR VIEWS ────────────────────────────────────────────────────────────

@login_required
def doctor_list_admin(request):
    """Admin view of all doctors."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    doctors = Doctor.objects.select_related('user', 'specialization').all()
    return render(request, 'clinical/doctor_list_admin.html', {'doctors': doctors})


@login_required
def doctor_create(request):
    """Admin creates a new doctor account."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    form = DoctorCreationForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            doctor = form.save()
            # Send welcome email to doctor
            try:
                send_mail(
                    subject=f'Welcome to {settings.SITE_NAME}',
                    message=f"""
Dear Dr. {doctor.user.username},

Your doctor account has been created on {settings.SITE_NAME}.

Login Details:
Email: {doctor.user.email}
Temporary Password: {form.cleaned_data['password']}

Please login and change your password immediately.
Login URL: {settings.SITE_DOMAIN}/users/login/

Best regards,
{settings.SITE_NAME} Admin Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[doctor.user.email],
                    fail_silently=True,
                )
            except Exception:
                pass

            messages.success(request, f'Doctor account created for Dr. {doctor.user.username}!')
            return redirect('clinical:doctor_list_admin')
        else:
            messages.error(request, 'Please fix the errors below.')

    return render(request, 'clinical/doctor_create.html', {'form': form})


@login_required
def doctor_edit(request, pk):
    """Admin edits doctor profile."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    doctor = get_object_or_404(Doctor, pk=pk)
    form = DoctorEditForm(request.POST or None, request.FILES or None, instance=doctor)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Doctor profile updated!')
        return redirect('clinical:doctor_list_admin')

    return render(request, 'clinical/doctor_edit.html', {'form': form, 'doctor': doctor})


@login_required
def doctor_delete(request, pk):
    """Admin deletes doctor."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        doctor.user.delete()  # Deletes user and doctor (cascade)
        messages.success(request, 'Doctor deleted successfully!')
        return redirect('clinical:doctor_list_admin')

    return render(request, 'clinical/doctor_confirm_delete.html', {'doctor': doctor})


# ─── DOCTOR SCHEDULE VIEWS ───────────────────────────────────────────────────

@login_required
def schedule_list(request):
    """Admin manages doctor schedules."""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    schedules = DoctorSchedule.objects.select_related('doctor__user', 'shift').all()
    form = DoctorScheduleForm()

    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule added!')
            return redirect('clinical:schedule_list')
        else:
            messages.error(request, 'Error adding schedule. Doctor may already have a schedule for this day.')

    return render(request, 'clinical/schedule_list.html', {'schedules': schedules, 'form': form})


@login_required
def schedule_edit(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    schedule = get_object_or_404(DoctorSchedule, pk=pk)
    form = DoctorScheduleForm(request.POST or None, instance=schedule)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Schedule updated!')
        return redirect('clinical:schedule_list')

    return render(request, 'clinical/schedule_edit.html', {'form': form, 'schedule': schedule})


@login_required
def schedule_delete(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    schedule = get_object_or_404(DoctorSchedule, pk=pk)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted!')
        return redirect('clinical:schedule_list')

    return render(request, 'clinical/schedule_confirm_delete.html', {'schedule': schedule})


# ─── DOCTOR LEAVE VIEWS ──────────────────────────────────────────────────────

@login_required
def doctor_leave(request):
    """Doctor marks their own leave days."""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    doctor = get_object_or_404(Doctor, user=request.user)
    leaves = DoctorLeave.objects.filter(doctor=doctor).order_by('-date')
    form = DoctorLeaveForm()

    if request.method == 'POST':
        form = DoctorLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.doctor = doctor
            leave.save()
            messages.success(request, 'Leave added successfully!')
            return redirect('clinical:doctor_leave')
        else:
            messages.error(request, 'Error adding leave. You may already have leave on this date.')

    return render(request, 'clinical/doctor_leave.html', {'leaves': leaves, 'form': form, 'doctor': doctor})


@login_required
def doctor_leave_delete(request, pk):
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    leave = get_object_or_404(DoctorLeave, pk=pk, doctor__user=request.user)
    if request.method == 'POST':
        leave.delete()
        messages.success(request, 'Leave cancelled!')
        return redirect('clinical:doctor_leave')

    return render(request, 'clinical/leave_confirm_delete.html', {'leave': leave})


# ─── PUBLIC DOCTOR SEARCH ────────────────────────────────────────────────────

@login_required
def doctor_search(request):
    """Patients search for doctors."""
    form = DoctorSearchForm(request.GET or None)
    doctors = Doctor.objects.filter(is_available=True).select_related('user', 'specialization')

    if form.is_valid():
        specialization = form.cleaned_data.get('specialization')
        name = form.cleaned_data.get('name')

        if specialization:
            doctors = doctors.filter(specialization=specialization)
        if name:
            doctors = doctors.filter(user__username__icontains=name)

    return render(request, 'clinical/doctor_search.html', {
        'doctors': doctors,
        'form': form
    })


@login_required
def doctor_detail(request, pk):
    """Public doctor detail page."""
    doctor = get_object_or_404(Doctor, pk=pk, is_available=True)
    schedules = DoctorSchedule.objects.filter(doctor=doctor, is_active=True).select_related('shift')
    try:
        from reviews.models import Review
        recent_reviews = Review.objects.filter(doctor=doctor).select_related('patient').order_by('-created_at')[:5]
    except Exception:
        recent_reviews = []

    return render(request, 'clinical/doctor_detail.html', {
        'doctor': doctor,
        'schedules': schedules,
        'recent_reviews': recent_reviews,
    })



@login_required
def doctor_edit_own_profile(request):
    """Doctor edits their own profile."""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    doctor = get_object_or_404(Doctor, user=request.user)
    form = DoctorEditForm(request.POST or None, request.FILES or None, instance=doctor)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:doctor_dashboard')
        else:
            messages.error(request, 'Please fix the errors below.')

    return render(request, 'clinical/doctor_edit_own_profile.html', {
        'form': form,
        'doctor': doctor
    })