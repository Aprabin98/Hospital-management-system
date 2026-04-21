"""API views for authentication"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import hashlib
from .models import User, TwoFactorCode, LoginAttempt
from audit.utils import log_audit_event
from .security import is_identifier_locked, clear_attempts, register_failed_attempt
from .utils import send_password_reset_email


def _parse_page_params(request, default_page=1, default_page_size=20, max_page_size=100):
    try:
        page = int(request.query_params.get('page', default_page))
    except (TypeError, ValueError):
        page = default_page

    try:
        page_size = int(request.query_params.get('page_size', default_page_size))
    except (TypeError, ValueError):
        page_size = default_page_size

    page = max(1, page)
    page_size = max(1, min(max_page_size, page_size))
    return page, page_size


@api_view(['POST'])
@permission_classes([AllowAny])
@require_http_methods(["POST"])
def login_api(request):
    """
    API endpoint for user login.
    
    Expected POST data:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Returns:
    {
        "token": "jwt_token",
        "user": {
            "id": 1,
            "email": "user@example.com",
            "role": "patient",
            "first_name": "John",
            "last_name": "Doe"
        },
        "role": "patient"
    }
    """
    from .views import _two_factor_required, _issue_two_factor_code
    
    email = (request.data.get('email') or '').strip().lower()
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'detail': 'Email and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    duplicate_window = int(getattr(settings, 'LOGIN_DUPLICATE_WINDOW_SECONDS', 15))
    now = timezone.now()
    fingerprint = hashlib.sha256(f"{(email or '').strip().lower()}|{password}".encode('utf-8')).hexdigest()
    last_fingerprint = request.session.get('api_last_login_fingerprint')
    last_at_raw = request.session.get('api_last_login_attempt_at')

    if last_fingerprint and last_at_raw:
        try:
            last_at = timezone.datetime.fromisoformat(last_at_raw)
            if timezone.is_naive(last_at):
                last_at = timezone.make_aware(last_at, timezone.get_current_timezone())
            if last_fingerprint == fingerprint and (now - last_at).total_seconds() < duplicate_window:
                return Response(
                    {'detail': 'Duplicate login submission ignored. Please wait before retrying.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
        except Exception:
            pass

    request.session['api_last_login_fingerprint'] = fingerprint
    request.session['api_last_login_attempt_at'] = now.isoformat()
    
    # Authenticate user
    user = authenticate(request, email=email, password=password)
    identifier_locked = is_identifier_locked(email)
    
    if user is not None:
        if not user.is_active:
            return Response(
                {'detail': 'Account is inactive.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        clear_attempts(email)
        
        # Check if two-factor authentication is required
        if _two_factor_required(user):
            _issue_two_factor_code(user, request)
            return Response(
                {'detail': 'Two-factor authentication required. Code sent to email.'},
                status=status.HTTP_202_ACCEPTED
            )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Log audit event
        log_audit_event(
            action='LOGIN',
            request=request,
            description='User logged in via API.',
            target={
                'model_name': 'users.user',
                'object_id': str(user.id),
                'object_repr': user.email,
            },
        )
        
        return Response(
            {
                'token': access_token,
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'role': user.role,
            },
            status=status.HTTP_200_OK
        )
    else:
        if identifier_locked:
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
            return Response(
                {'detail': 'Too many failed attempts. Try again in 30 minutes.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Register failed attempt
        register_failed_attempt(
            email, 
            ip_address=request.META.get('REMOTE_ADDR', ''),
            request=request
        )
        
        # Log failed attempt
        log_audit_event(
            action='LOGIN_FAILED',
            request=request,
            description='Failed login attempt.',
            target={
                'model_name': 'users.user',
                'object_id': '',
                'object_repr': email,
            },
            metadata={
                'identifier': email,
                'reason': 'invalid_credentials',
            },
        )
        
        return Response(
            {'detail': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@require_http_methods(["POST"])
def two_factor_verify_api(request):
    """Verify OTP for API login flow and issue JWT tokens."""
    email = (request.data.get('email') or '').strip().lower()
    otp = (request.data.get('otp') or '').strip()

    if not email or not otp:
        return Response({'detail': 'Email and otp are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if not otp.isdigit() or len(otp) != 6:
        return Response({'detail': 'Invalid OTP format.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    challenge = (
        TwoFactorCode.objects
        .filter(user=user, is_used=False)
        .order_by('-created_at')
        .first()
    )
    if not challenge:
        return Response({'detail': 'No pending verification code. Please login again.'}, status=status.HTTP_400_BAD_REQUEST)

    if challenge.is_expired():
        challenge.is_used = True
        challenge.save(update_fields=['is_used'])
        return Response({'detail': 'Verification code expired. Please login again.'}, status=status.HTTP_400_BAD_REQUEST)

    if otp != challenge.code:
        challenge.attempts += 1
        max_attempts = getattr(settings, 'TWO_FACTOR_MAX_ATTEMPTS', 5)
        if challenge.attempts >= max_attempts:
            challenge.is_used = True
        challenge.save(update_fields=['attempts', 'is_used'])
        return Response({'detail': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

    challenge.is_used = True
    challenge.save(update_fields=['is_used'])

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    log_audit_event(
        action='LOGIN',
        request=request,
        description='User completed API 2FA login.',
        target={
            'model_name': 'users.user',
            'object_id': str(user.id),
            'object_repr': user.email,
        },
        metadata={'two_factor': True},
    )

    return Response(
        {
            'token': access_token,
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'role': user.role,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
@require_http_methods(["POST"])
def two_factor_resend_api(request):
    """Resend OTP for API login flow."""
    from .views import _issue_two_factor_code

    email = (request.data.get('email') or '').strip().lower()
    if not email:
        return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not user.is_active:
        return Response({'detail': 'Account is inactive.'}, status=status.HTTP_403_FORBIDDEN)

    _issue_two_factor_code(user, request)
    return Response({'detail': 'Verification code sent.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def logout_api(request):
    """
    API endpoint for user logout.
    
    For JWT-based authentication, logout is typically handled on the client side
    by removing the token from localStorage.
    
    Returns:
    {
        "detail": "Successfully logged out."
    }
    """
    user = request.user
    
    # Log audit event
    log_audit_event(
        action='LOGOUT',
        request=request,
        description='User logged out via API.',
        target={
            'model_name': 'users.user',
            'object_id': str(user.id),
            'object_repr': user.email,
        },
    )
    
    return Response(
        {'detail': 'Successfully logged out.'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
@require_http_methods(["POST"])
def register_api(request):
    """
    API endpoint for user registration.
    
    Expected POST data:
    {
        "email": "user@example.com",
        "password": "password123",
        "password_confirm": "password123",
        "first_name": "John",
        "last_name": "Doe",
        "role": "patient"
    }
    
    Returns:
    {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "patient"
    }
    """
    from .forms import PatientRegistrationForm
    
    data = request.data
    
    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name']
    for field in required_fields:
        if not data.get(field):
            return Response(
                {'detail': f'{field} is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Check if user already exists
    if User.objects.filter(email=data.get('email')).exists():
        return Response(
            {'detail': 'Email already registered.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    username = (data.get('username') or '').strip()
    if not username:
        base = (data.get('email') or '').split('@')[0].strip() or 'user'
        username = base
        suffix = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{suffix}"
            suffix += 1

    # Public self-registration is patient-only.
    role = 'PATIENT'

    # Create user
    try:
        user = User.objects.create_user(
            email=data.get('email'),
            username=username,
            password=data.get('password'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=role,
            is_active=True,
        )

        # Ensure patient profile exists for patient role logins.
        if role == 'PATIENT':
            from .models import PatientProfile
            full_name = f"{user.first_name} {user.last_name}".strip() or user.username
            PatientProfile.objects.get_or_create(user=user, defaults={'full_name': full_name})
        
        # Log audit event
        log_audit_event(
            action='REGISTRATION',
            request=request,
            description='New user registered via API.',
            target={
                'model_name': 'users.user',
                'object_id': str(user.id),
                'object_repr': user.email,
            },
        )
        
        return Response(
            {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {'detail': f'Registration failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@require_http_methods(["POST"])
def password_reset_request_api(request):
    """Request password reset by email."""
    email = (request.data.get('email') or '').strip().lower()
    if not email:
        return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response({'detail': 'No account found with this email.'}, status=status.HTTP_404_NOT_FOUND)

    sent = send_password_reset_email(user, request)
    if not sent:
        return Response({'detail': 'Failed to send reset email. Try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'detail': 'Password reset email sent successfully.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@require_http_methods(["POST"])
def password_reset_confirm_api(request):
    """Set a new password using reset token."""
    user_id = request.data.get('user_id')
    token = (request.data.get('token') or '').strip()
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    if not user_id or not token or not password or not confirm_password:
        return Response({'detail': 'user_id, token, password and confirm_password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if password != confirm_password:
        return Response({'detail': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    if user.activation_token != token:
        return Response({'detail': 'Invalid or expired reset token.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(password)
    user.activation_token = None
    user.save()

    clear_attempts(user.email)
    return Response({'detail': 'Password reset successful. Please login.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def current_user_api(request):
    """
    API endpoint to get current authenticated user info.
    
    Returns:
    {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "patient"
    }
    """
    user = request.user
    return Response(
        {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def login_attempts_admin_api(request):
    """Admin-only login attempt monitoring endpoint."""
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 30))
    except (TypeError, ValueError):
        page = 1
        page_size = 30

    page = max(1, page)
    page_size = max(1, min(100, page_size))

    status_filter = (request.query_params.get('status') or '').strip().lower()
    query = (request.query_params.get('q') or '').strip()

    attempts = LoginAttempt.objects.all().order_by('-last_attempt')
    now = timezone.now()

    if status_filter == 'locked':
        attempts = attempts.filter(locked_until__gt=now)
    elif status_filter == 'open':
        attempts = attempts.exclude(locked_until__gt=now)

    if query:
        attempts = attempts.filter(identifier__icontains=query)

    total_count = attempts.count()
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    locked_count = LoginAttempt.objects.filter(locked_until__gt=now).count()
    failed_total = LoginAttempt.objects.filter(failed_count__gt=0).count()

    results = []
    for item in attempts[start_idx:end_idx]:
        is_locked = bool(item.locked_until and item.locked_until > now)
        results.append(
            {
                'id': item.id,
                'identifier': item.identifier,
                'failed_count': item.failed_count,
                'last_ip': item.last_ip,
                'last_attempt': item.last_attempt.isoformat() if item.last_attempt else None,
                'locked_until': item.locked_until.isoformat() if item.locked_until else None,
                'is_locked': is_locked,
                'status': 'LOCKED' if is_locked else ('FAILED' if item.failed_count > 0 else 'CLEAR'),
            }
        )

    return Response(
        {
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'locked_count': locked_count,
            'failed_count': failed_total,
            'results': results,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def dashboard_stats_api(request):
    """
    API endpoint to get dashboard statistics.
    
    Returns:
    {
        "total_patients": 10,
        "total_appointments": 25,
        "pending_appointments": 5,
        "total_doctors": 4
    }
    """
    from appointments.models import Appointment
    from clinical.models import Doctor
    from users.models import PatientProfile
    from django.db.models import Q
    from django.utils import timezone
    
    try:
        role = request.user.role

        if role == 'PATIENT':
            patient = request.user.patient_profile
            appointments_qs = Appointment.objects.filter(patient=patient)
            total_patients = 1
            total_doctors = appointments_qs.values('doctor').distinct().count()
        elif role == 'DOCTOR':
            doctor = request.user.doctor_profile
            appointments_qs = Appointment.objects.filter(doctor=doctor)
            total_patients = appointments_qs.values('patient').distinct().count()
            total_doctors = 1
        elif role in ['ADMIN', 'RECEPTIONIST', 'NURSE']:
            appointments_qs = Appointment.objects.all()
            total_patients = PatientProfile.objects.count()
            total_doctors = Doctor.objects.count()
        else:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        total_appointments = appointments_qs.count()

        # Pending workload should include both new and confirmed upcoming appointments.
        pending_appointments = appointments_qs.filter(
            Q(status='PENDING') | Q(status='CONFIRMED')
        ).count()
        
        return Response(
            {
                'total_patients': total_patients,
                'total_appointments': total_appointments,
                'pending_appointments': pending_appointments,
                'total_doctors': total_doctors,
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {
                'total_patients': 0,
                'total_appointments': 0,
                'pending_appointments': 0,
                'total_doctors': 0,
            },
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def patients_list_api(request):
    """
    API endpoint to get patients list with pagination.
    
    Query parameters:
    - page: Page number (default: 1)
    - page_size: Number of results per page (default: 10)
    
    Returns:
    {
        "count": 10,
        "next": "http://...",
        "previous": null,
        "results": [...]
    }
    """
    from .api_serializers import PatientProfileSerializer
    from .models import PatientProfile

    if request.user.role not in ['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'NURSE']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    page, page_size = _parse_page_params(request, default_page_size=20, max_page_size=100)
    
    patients = PatientProfile.objects.select_related('user').filter(user__role='PATIENT')

    query = (request.GET.get('q') or '').strip()
    if query:
        from django.db.models import Q
        if query.isdigit():
            patients = patients.filter(
                Q(id=int(query))
                | Q(full_name__icontains=query)
                | Q(user__email__icontains=query)
                | Q(phone__icontains=query)
            )
        else:
            patients = patients.filter(
                Q(full_name__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(user__email__icontains=query)
                | Q(user__username__icontains=query)
                | Q(phone__icontains=query)
                | Q(blood_group__icontains=query)
            )
    total_count = patients.count()
    
    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_patients = patients[start_idx:end_idx]
    
    serializer = PatientProfileSerializer(paginated_patients, many=True)
    
    return Response(
        {
            'count': total_count,
            'next': f'/api/patients/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/patients/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def patient_duplicate_check_api(request):
    """Detect potential duplicate patients using fuzzy matching."""
    if request.user.role not in ['ADMIN', 'RECEPTIONIST', 'NURSE']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    full_name = (request.query_params.get('full_name') or '').strip()
    date_of_birth = (request.query_params.get('date_of_birth') or '').strip()
    phone = (request.query_params.get('phone') or '').strip()
    email = (request.query_params.get('email') or '').strip().lower()

    if not full_name or not date_of_birth:
        return Response(
            {'detail': 'full_name and date_of_birth are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from datetime import date
    from appointments.patient_matcher import PatientMatchingService
    try:
        parsed_dob = date.fromisoformat(date_of_birth)
    except ValueError:
        return Response({'detail': 'Invalid date_of_birth format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    matches = PatientMatchingService.find_potential_matches(
        full_name=full_name,
        date_of_birth=parsed_dob,
        phone=phone or None,
        email=email or None,
    )

    return Response(
        {
            'count': len(matches),
            'results': [
                {
                    'patient_id': patient.id,
                    'patient_name': patient.full_name,
                    'date_of_birth': patient.date_of_birth,
                    'phone': patient.phone,
                    'email': patient.user.email,
                    'match_type': match_type,
                    'confidence': float(confidence),
                }
                for patient, match_type, confidence in matches
            ],
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def patient_allergies_api(request, patient_id):
    """List or create allergies for a patient."""
    from .models import PatientProfile, PatientAllergy
    from .api_serializers import PatientAllergySerializer

    try:
        patient = PatientProfile.objects.get(id=patient_id, user__role='PATIENT')
    except PatientProfile.DoesNotExist:
        return Response({'detail': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role == 'PATIENT':
        own_profile = PatientProfile.objects.filter(user=request.user).first()
        if not own_profile or own_profile.id != patient.id:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
    elif request.user.role not in ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        queryset = PatientAllergy.objects.filter(patient=patient).order_by('-updated_at')
        serializer = PatientAllergySerializer(queryset, many=True)
        return Response({'count': queryset.count(), 'results': serializer.data}, status=status.HTTP_200_OK)

    # POST
    if request.user.role not in ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']:
        return Response({'detail': 'Only clinical/front-desk staff can add allergies.'}, status=status.HTTP_403_FORBIDDEN)

    payload = dict(request.data)
    payload['patient'] = patient.id
    serializer = PatientAllergySerializer(data=payload)
    if not serializer.is_valid():
        return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    allergy = serializer.save(recorded_by=request.user)
    log_audit_event(
        action='CREATE',
        target=allergy,
        description='Patient allergy created via API.',
        metadata={'patient_id': patient.id, 'allergen': allergy.allergen},
        actor=request.user,
        request=request,
    )
    return Response(PatientAllergySerializer(allergy).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@require_http_methods(["PATCH", "DELETE"])
def patient_allergy_detail_api(request, patient_id, allergy_id):
    """Update or delete a specific allergy for a patient."""
    from .models import PatientProfile, PatientAllergy
    from .api_serializers import PatientAllergySerializer

    if request.user.role not in ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        patient = PatientProfile.objects.get(id=patient_id, user__role='PATIENT')
    except PatientProfile.DoesNotExist:
        return Response({'detail': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        allergy = PatientAllergy.objects.get(id=allergy_id, patient=patient)
    except PatientAllergy.DoesNotExist:
        return Response({'detail': 'Allergy not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        allergy_repr = str(allergy)
        allergy.delete()
        log_audit_event(
            action='DELETE',
            target={'model_name': 'users.patientallergy', 'object_id': str(allergy_id), 'object_repr': allergy_repr},
            description='Patient allergy deleted via API.',
            metadata={'patient_id': patient.id},
            actor=request.user,
            request=request,
        )
        return Response({'detail': 'Allergy deleted successfully.'}, status=status.HTTP_200_OK)

    serializer = PatientAllergySerializer(allergy, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    updated = serializer.save()
    log_audit_event(
        action='UPDATE',
        target=updated,
        description='Patient allergy updated via API.',
        metadata={'patient_id': patient.id, 'allergy_id': updated.id},
        actor=request.user,
        request=request,
    )
    return Response(PatientAllergySerializer(updated).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def patient_detail_api(request, patient_id):
    """
    API endpoint to get patient detail.
    
    Returns patient profile with health records.
    """
    from .api_serializers import PatientProfileSerializer
    from .models import PatientProfile

    if request.user.role not in ['PATIENT', 'ADMIN', 'DOCTOR', 'RECEPTIONIST', 'NURSE']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        patient = PatientProfile.objects.select_related('user').get(id=patient_id, user__role='PATIENT')

        if request.user.role == 'PATIENT':
            own_profile = PatientProfile.objects.filter(user=request.user).first()
            if not own_profile or own_profile.id != patient.id:
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PatientProfileSerializer(patient)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except PatientProfile.DoesNotExist:
        return Response(
            {'detail': 'Patient not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ================== PROFILE EDIT ENDPOINT ==================

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "PUT", "PATCH"])
def profile_edit_api(request):
    """
    Get or update authenticated user's profile.
    
    GET: Returns current user profile with linked patient profile
    PUT/PATCH: Updates user and patient profile details
    """
    from .api_serializers import UserSerializer, PatientProfileSerializer, DoctorProfileSerializer
    from .models import PatientProfile
    from clinical.models import Doctor, Specialization
    
    user = request.user
    
    try:
        # Try to get patient profile if exists
        patient_profile = PatientProfile.objects.select_related('user').get(user=user)
    except PatientProfile.DoesNotExist:
        patient_profile = None

    doctor_profile = None
    if user.role == 'DOCTOR':
        doctor_profile, _ = Doctor.objects.get_or_create(user=user)
        doctor_profile = Doctor.objects.select_related('user', 'specialization').get(pk=doctor_profile.pk)
    else:
        try:
            doctor_profile = Doctor.objects.select_related('user', 'specialization').get(user=user)
        except Doctor.DoesNotExist:
            doctor_profile = None
    
    if request.method == 'GET':
        # Return user profile with patient info if available
        user_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
        }
        
        if patient_profile:
            patient_serializer = PatientProfileSerializer(patient_profile)
            user_data['patient_profile'] = patient_serializer.data

        if doctor_profile:
            doctor_serializer = DoctorProfileSerializer(doctor_profile, context={'request': request})
            user_data['doctor_profile'] = doctor_serializer.data
            user_data['specialization_choices'] = [
                {'id': spec.id, 'name': spec.name}
                for spec in Specialization.objects.filter(is_active=True).order_by('name')
            ]
        
        return Response(user_data, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        # Update user profile
        partial = request.method == 'PATCH'
        
        # Update user fields
        update_fields = {}
        if 'first_name' in request.data:
            update_fields['first_name'] = request.data.get('first_name')
        if 'last_name' in request.data:
            update_fields['last_name'] = request.data.get('last_name')
        if 'username' in request.data:
            update_fields['username'] = request.data.get('username')
        
        if update_fields:
            for field, value in update_fields.items():
                setattr(user, field, value)
            user.save()
        
        # Update patient profile fields if patient profile exists
        if patient_profile and 'patient_profile' in request.data:
            patient_data = request.data.get('patient_profile', {})
            serializer = PatientProfileSerializer(patient_profile, data=patient_data, partial=True)
            if not serializer.is_valid():
                return Response(
                    {'detail': 'Validation error', 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.save()

        # Update doctor profile fields if doctor profile exists.
        # Supports both nested JSON payload and multipart top-level fields.
        if doctor_profile:
            doctor_data = {}

            nested_doctor_data = request.data.get('doctor_profile')
            if isinstance(nested_doctor_data, dict):
                doctor_data.update(nested_doctor_data)

            doctor_field_map = {
                'doctor_specialization': 'specialization',
                'doctor_consultation_fee': 'consultation_fee',
                'doctor_experience_years': 'experience_years',
                'doctor_phone': 'phone',
                'doctor_bio': 'bio',
                'doctor_is_available': 'is_available',
            }

            for incoming_key, target_key in doctor_field_map.items():
                if incoming_key in request.data:
                    doctor_data[target_key] = request.data.get(incoming_key)

            if 'doctor_photo' in request.FILES:
                doctor_data['photo'] = request.FILES.get('doctor_photo')

            if doctor_data.get('specialization') == '':
                doctor_data['specialization'] = None

            if doctor_data:
                serializer = DoctorProfileSerializer(doctor_profile, data=doctor_data, partial=True)
                if not serializer.is_valid():
                    return Response(
                        {'detail': 'Validation error', 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                serializer.save()
        
        # Log audit event
        log_audit_event(
            action='PROFILE_UPDATE',
            request=request,
            description='User updated profile',
            target={
                'model_name': 'users.user',
                'object_id': str(user.id),
                'object_repr': user.email,
            },
        )
        
        # Return updated profile
        user_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
        }
        
        if patient_profile:
            patient_profile.refresh_from_db()
            patient_serializer = PatientProfileSerializer(patient_profile)
            user_data['patient_profile'] = patient_serializer.data

        if doctor_profile:
            doctor_profile.refresh_from_db()
            doctor_serializer = DoctorProfileSerializer(doctor_profile, context={'request': request})
            user_data['doctor_profile'] = doctor_serializer.data
            user_data['specialization_choices'] = [
                {'id': spec.id, 'name': spec.name}
                for spec in Specialization.objects.filter(is_active=True).order_by('name')
            ]
        
        return Response(user_data, status=status.HTTP_200_OK)
