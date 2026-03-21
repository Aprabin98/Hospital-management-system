from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .forms import (
    PatientRegistrationForm, LoginForm,
    PatientProfileForm, PasswordResetRequestForm, SetNewPasswordForm
)
from .utils import send_activation_email, send_password_reset_email
from .models import PatientProfile
from .security import clear_attempts, is_identifier_locked, register_failed_attempt

User = get_user_model()


# ─── REGISTRATION ────────────────────────────────────────────────────────────

def register_view(request):
    """Patient registration view."""
    if request.user.is_authenticated:
        return redirect('users:dashboard')

    form = PatientRegistrationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            send_activation_email(user, request)
            messages.success(
                request,
                'Account created! Please check your email to activate your account.'
            )
            return redirect('users:login')
        else:
            messages.error(request, 'Please fix the errors below.')

    return render(request, 'users/register.html', {'form': form})


# ─── EMAIL ACTIVATION ────────────────────────────────────────────────────────

def activate_account(request, user_id, token):
    """Activate user account via email link."""
    user = get_object_or_404(User, id=user_id)

    if user.is_active:
        messages.info(request, 'Your account is already activated. Please login.')
        return redirect('users:login')

    if user.activation_token == token:
        user.is_active = True
        user.activation_token = None
        user.save()
        messages.success(request, 'Account activated successfully! You can now login.')
    else:
        messages.error(request, 'Invalid or expired activation link.')

    return redirect('users:login')


# ─── LOGIN ───────────────────────────────────────────────────────────────────

def login_view(request):
    """Login view - redirects based on role."""
    if request.user.is_authenticated:
        return redirect('users:dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            if is_identifier_locked(email):
                messages.error(request, 'Too many failed attempts. Try again in 30 minutes.')
                return render(request, 'users/login.html', {'form': form})

            user = authenticate(request, email=email, password=password)

            if user is not None:
                if user.is_active:
                    clear_attempts(email)
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('users:dashboard')
                else:
                    messages.error(
                        request,
                        'Your account is not activated. Please check your email.'
                    )
            else:
                ip_address = request.META.get('REMOTE_ADDR', '')
                register_failed_attempt(email, ip_address=ip_address)
                messages.error(request, 'Invalid email or password.')

    return render(request, 'users/login.html', {'form': form})


# ─── LOGOUT ──────────────────────────────────────────────────────────────────

@login_required
def logout_view(request):
    """Logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('users:login')


# ─── DASHBOARD (Role-based redirect) ─────────────────────────────────────────

@login_required
def dashboard_view(request):
    user = request.user
    if user.role == 'PATIENT':
        return redirect('users:patient_dashboard')
    elif user.role == 'DOCTOR':
        return redirect('users:doctor_dashboard')
    elif user.role == 'RECEPTIONIST':
        return redirect('users:receptionist_dashboard')
    elif user.role == 'ADMIN':
        return redirect('users:admin_dashboard')
    elif user.role == 'LAB_TECHNICIAN':
        return redirect('users:lab_technician_dashboard')
    else:
        logout(request)
        return redirect('users:login')
    

# ─── PATIENT DASHBOARD ───────────────────────────────────────────────────────

@login_required
def patient_dashboard(request):
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    try:
        profile = request.user.patient_profile
    except PatientProfile.DoesNotExist:
        profile = PatientProfile.objects.create(
            user=request.user,
            full_name=request.user.username
        )

    # Import here to avoid circular imports
    from appointments.models import Appointment
    from datetime import date

    all_appointments = Appointment.objects.filter(
        patient=profile
    ).select_related('doctor__user').order_by('-date')

    from payments.models import Payment

    unpaid_count = Payment.objects.filter(
        patient=profile,
        status='UNPAID'
    ).count()

    context = {
        'profile': profile,
        'user': request.user,
        'total_appointments': all_appointments.count(),
        'upcoming_appointments': all_appointments.filter(
            date__gte=date.today(),
            status__in=['PENDING', 'CONFIRMED']
        ).count(),
        'recent_appointments': all_appointments[:5],
        'unpaid_count': unpaid_count,
    }
    
    return render(request, 'users/patient_dashboard.html', context)


# ─── DOCTOR DASHBOARD ────────────────────────────────────────────────────────

@login_required
def doctor_dashboard(request):
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    from appointments.models import Appointment
    from datetime import date

    try:
        doctor = request.user.doctor_profile
        all_appointments = Appointment.objects.filter(doctor=doctor)
        today = date.today()

        todays_appointments = all_appointments.filter(
            date=today,
            status__in=['PENDING', 'CONFIRMED']
        ).select_related('patient').order_by('start_time')

        context = {
            'user': request.user,
            'todays_count': todays_appointments.count(),
            'upcoming_count': all_appointments.filter(
                date__gte=today,
                status__in=['PENDING', 'CONFIRMED']
            ).count(),
            'completed_count': all_appointments.filter(
                status='COMPLETED'
            ).count(),
            'todays_appointments': todays_appointments,
        }
    except Exception:
        context = {
            'user': request.user,
            'todays_count': 0,
            'upcoming_count': 0,
            'completed_count': 0,
            'todays_appointments': [],
        }

    return render(request, 'users/doctor_dashboard.html', context)


# ─── ADMIN DASHBOARD ─────────────────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    from appointments.models import Appointment
    from datetime import date

    User = get_user_model()

    context = {
        'total_patients': User.objects.filter(role='PATIENT').count(),
        'total_doctors': User.objects.filter(role='DOCTOR').count(),
        'todays_appointments': Appointment.objects.filter(
            date=date.today()
        ).count(),
        'total_appointments': Appointment.objects.count(),
    }
    return render(request, 'users/admin_dashboard.html', context)

# ─── LAB TECHNICIAN DASHBOARD ─────────────────────────────────────────────────

@login_required
def lab_technician_dashboard(request):
    if request.user.role != 'LAB_TECHNICIAN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    from lab.models import TestBooking
    from datetime import date
    today = date.today()

    context = {
        'user': request.user,
        'todays_count': TestBooking.objects.filter(date=today).count(),
        'pending_count': TestBooking.objects.filter(
            status__in=['PENDING', 'SAMPLE_COLLECTED', 'PROCESSING']
        ).count(),
        'completed_count': TestBooking.objects.filter(
            date=today, status='COMPLETED'
        ).count(),
    }
    return render(request, 'users/lab_dashboard.html', context)

# ─── PROFILE EDIT ────────────────────────────────────────────────────────────

@login_required
def edit_profile(request):
    """Edit patient profile."""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    profile = request.user.patient_profile
    form = PatientProfileForm(request.POST or None, request.FILES or None, instance=profile)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:patient_dashboard')
        else:
            messages.error(request, 'Please fix the errors below.')

    return render(request, 'users/edit_profile.html', {'form': form, 'profile': profile})


# ─── PASSWORD RESET ──────────────────────────────────────────────────────────

def password_reset_request(request):
    """Request password reset email."""
    form = PasswordResetRequestForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            sent = send_password_reset_email(user, request)
            if sent:
                messages.success(request, 'Password reset email sent! Check your inbox.')
            else:
                messages.error(request, 'Failed to send email. Try again later.')
            return redirect('users:login')

    return render(request, 'users/password_reset_request.html', {'form': form})


def password_reset_confirm(request, user_id, token):
    """Set new password after clicking reset link."""
    user = get_object_or_404(User, id=user_id)

    if user.activation_token != token:
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('users:login')

    form = SetNewPasswordForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user.set_password(form.cleaned_data['password'])
            user.activation_token = None
            user.save()
            messages.success(request, 'Password reset successful! Please login.')
            return redirect('users:login')

    return render(request, 'users/password_reset_confirm.html', {'form': form})

@login_required
def receptionist_dashboard(request):
    if request.user.role != 'RECEPTIONIST':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')
    return render(request, 'users/receptionist_dashboard.html', {'user': request.user})