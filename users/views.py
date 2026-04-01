from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
import secrets

from .forms import (
    PatientRegistrationForm, LoginForm,
    PatientProfileForm, PasswordResetRequestForm, SetNewPasswordForm,
    TwoFactorVerifyForm
)
from .utils import send_activation_email, send_password_reset_email
from .models import PatientProfile, TwoFactorCode
from .security import clear_attempts, is_identifier_locked, register_failed_attempt
from .tasks import send_email_task
from notifications.utils import build_two_factor_otp_whatsapp, send_whatsapp_message
from audit.utils import log_audit_event

User = get_user_model()


def _two_factor_required(user):
    bypass_emails = set(getattr(settings, 'TWO_FACTOR_BYPASS_EMAILS', set()))
    if (user.email or '').strip().lower() in bypass_emails:
        return False

    required_roles = set(getattr(settings, 'TWO_FACTOR_REQUIRED_ROLES', []))
    return user.role in required_roles


def _issue_two_factor_code(user, request):
    TwoFactorCode.objects.filter(user=user, is_used=False).update(is_used=True)

    code = f"{secrets.randbelow(1000000):06d}"
    expiry_minutes = getattr(settings, 'TWO_FACTOR_OTP_EXPIRY_MINUTES', 10)
    challenge = TwoFactorCode.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
    )

    if getattr(settings, 'PRINT_2FA_OTP_IN_TERMINAL', True):
        print(
            f"[MediMind 2FA OTP] user={user.email} code={code} "
            f"expires_in={expiry_minutes}m challenge_id={challenge.id}"
        )

    subject = f"{settings.SITE_NAME} Login Verification Code"
    message = (
        f"Hi {user.username},\n\n"
        f"Your login verification code is: {code}\n"
        f"This code expires in {expiry_minutes} minutes.\n\n"
        f"If you did not try to login, please reset your password immediately."
    )

    try:
        send_email_task.delay(subject, message, user.email)
    except Exception:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

    # Optional WhatsApp OTP notification based on available role profile phone.
    if getattr(settings, 'WHATSAPP_SEND_2FA_OTP', True):
        whatsapp_phone = ''
        if user.role == 'PATIENT':
            try:
                whatsapp_phone = user.patient_profile.phone
            except Exception:
                whatsapp_phone = ''
        elif user.role == 'DOCTOR':
            try:
                whatsapp_phone = user.doctor_profile.phone
            except Exception:
                whatsapp_phone = ''

        if whatsapp_phone:
            send_whatsapp_message(
                whatsapp_phone,
                build_two_factor_otp_whatsapp(user, code, expiry_minutes),
            )

    request.session['two_factor_user_id'] = user.id
    request.session['two_factor_challenge_id'] = challenge.id
    request.session['two_factor_backend'] = getattr(
        user,
        'backend',
        settings.AUTHENTICATION_BACKENDS[0],
    )
    request.session.set_expiry(60 * expiry_minutes)


def _clear_two_factor_session(request):
    request.session.pop('two_factor_user_id', None)
    request.session.pop('two_factor_challenge_id', None)
    request.session.pop('two_factor_backend', None)


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
                log_audit_event(
                    action='SECURITY',
                    request=request,
                    description='Blocked login attempt for locked identifier.',
                    target={
                        'model_name': 'users.loginattempt',
                        'object_id': '',
                        'object_repr': email,
                    },
                    metadata={
                        'identifier': email,
                        'reason': 'identifier_locked',
                    },
                )
                messages.error(request, 'Too many failed attempts. Try again in 30 minutes.')
                return render(request, 'users/login.html', {'form': form})

            user = authenticate(request, email=email, password=password)

            if user is not None:
                if user.is_active:
                    clear_attempts(email)
                    if _two_factor_required(user):
                        _issue_two_factor_code(user, request)
                        messages.info(request, 'Verification code sent to your email.')
                        return redirect('users:two_factor_verify')

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
                register_failed_attempt(email, ip_address=ip_address, request=request)
                messages.error(request, 'Invalid email or password.')

    return render(request, 'users/login.html', {'form': form})


# ─── LOGOUT ──────────────────────────────────────────────────────────────────

@login_required
def logout_view(request):
    """Logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('users:login')


def two_factor_verify(request):
    if request.user.is_authenticated:
        return redirect('users:dashboard')

    user_id = request.session.get('two_factor_user_id')
    challenge_id = request.session.get('two_factor_challenge_id')
    auth_backend = request.session.get('two_factor_backend')
    if not user_id or not challenge_id:
        messages.error(request, '2FA session expired. Please login again.')
        return redirect('users:login')

    user = get_object_or_404(User, id=user_id)
    challenge = get_object_or_404(TwoFactorCode, id=challenge_id, user=user, is_used=False)

    if challenge.is_expired():
        challenge.is_used = True
        challenge.save(update_fields=['is_used'])
        _clear_two_factor_session(request)
        messages.error(request, 'Verification code expired. Please login again.')
        return redirect('users:login')

    form = TwoFactorVerifyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code']
        if code != challenge.code:
            challenge.attempts += 1
            max_attempts = getattr(settings, 'TWO_FACTOR_MAX_ATTEMPTS', 5)
            if challenge.attempts >= max_attempts:
                challenge.is_used = True
                challenge.save(update_fields=['attempts', 'is_used'])
                _clear_two_factor_session(request)
                messages.error(request, 'Maximum verification attempts reached. Please login again.')
                return redirect('users:login')

            challenge.save(update_fields=['attempts'])
            messages.error(request, 'Invalid verification code.')
        else:
            challenge.is_used = True
            challenge.save(update_fields=['is_used'])
            _clear_two_factor_session(request)
            login(
                request,
                user,
                backend=auth_backend or settings.AUTHENTICATION_BACKENDS[0],
            )
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('users:dashboard')

    context = {
        'form': form,
        'masked_email': user.email[:3] + '***' + user.email[user.email.find('@'):],
    }
    return render(request, 'users/two_factor_verify.html', context)


@require_POST
def two_factor_resend(request):
    user_id = request.session.get('two_factor_user_id')
    if not user_id:
        messages.error(request, '2FA session expired. Please login again.')
        return redirect('users:login')

    user = get_object_or_404(User, id=user_id)
    _issue_two_factor_code(user, request)
    messages.success(request, 'A new verification code has been sent.')
    return redirect('users:two_factor_verify')


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


@login_required
def profile_view(request):
    """Redirect users to the appropriate profile page by role."""
    role = request.user.role
    if role == 'PATIENT':
        return redirect('users:edit_profile')
    if role == 'DOCTOR':
        return redirect('clinical:doctor_edit_own_profile')
    if role == 'RECEPTIONIST':
        return redirect('users:receptionist_dashboard')
    if role == 'ADMIN':
        return redirect('users:admin_dashboard')
    if role == 'LAB_TECHNICIAN':
        return redirect('users:lab_technician_dashboard')
    return redirect('users:dashboard')
    

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
    from appointments.models import Appointment, MedicalReportAnalysis
    from datetime import date

    all_appointments = Appointment.objects.filter(
        patient=profile
    ).select_related('doctor__user').order_by('-date')

    from payments.models import Payment
    from prescriptions.models import Prescription

    unpaid_count = Payment.objects.filter(
        patient=profile,
        status='UNPAID'
    ).count()
    prescription_count = Prescription.objects.filter(patient=profile).count()

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
        'prescription_count': prescription_count,
        'ai_reports_count': MedicalReportAnalysis.objects.filter(patient=profile).count(),
    }
    
    return render(request, 'users/patient_dashboard.html', context)


# ─── DOCTOR DASHBOARD ────────────────────────────────────────────────────────

@login_required
def doctor_dashboard(request):
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    from appointments.models import Appointment, MedicalReportAnalysis
    from reviews.models import Review
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
            'doctor_profile': doctor,
            'avg_rating': doctor.get_average_rating(),
            'total_reviews': Review.objects.filter(doctor=doctor).count(),
            'ai_reports_count': MedicalReportAnalysis.objects.count(),
        }
    except Exception:
        context = {
            'user': request.user,
            'todays_count': 0,
            'upcoming_count': 0,
            'completed_count': 0,
            'todays_appointments': [],
            'ai_reports_count': 0,
        }

    return render(request, 'users/doctor_dashboard.html', context)


# ─── ADMIN DASHBOARD ─────────────────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    from appointments.models import Appointment, MedicalReportAnalysis
    from datetime import date

    User = get_user_model()

    context = {
        'total_patients': User.objects.filter(role='PATIENT').count(),
        'total_doctors': User.objects.filter(role='DOCTOR').count(),
        'todays_appointments': Appointment.objects.filter(
            date=date.today()
        ).count(),
        'total_appointments': Appointment.objects.count(),
        'report_reader_total': MedicalReportAnalysis.objects.count(),
        'recent_report_analyses': MedicalReportAnalysis.objects.select_related(
            'patient__user', 'created_by'
        )[:20],
    }
    return render(request, 'users/admin_dashboard.html', context)

# ─── LAB TECHNICIAN DASHBOARD ─────────────────────────────────────────────────

@login_required
def lab_technician_dashboard(request):
    if request.user.role != 'LAB_TECHNICIAN':
        messages.error(request, 'Access denied.')
        return redirect('users:dashboard')

    from lab.models import TestBooking
    from appointments.models import MedicalReportAnalysis
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
        'ai_reports_count': MedicalReportAnalysis.objects.count(),
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

    from appointments.models import Appointment, MedicalReportAnalysis
    from clinical.models import Doctor
    from payments.models import Payment
    from datetime import date

    today = date.today()
    context = {
        'user': request.user,
        'todays_appointments': Appointment.objects.filter(date=today).count(),
        'checked_in_count': Appointment.objects.filter(
            date=today,
            status__in=['CONFIRMED', 'COMPLETED']
        ).count(),
        'pending_payments': Payment.objects.filter(status__in=['UNPAID', 'OVERDUE', 'PARTIALLY_PAID']).count(),
        'available_doctors': Doctor.objects.filter(is_available=True).count(),
        'ai_reports_count': MedicalReportAnalysis.objects.count(),
    }
    return render(request, 'users/receptionist_dashboard.html', context)