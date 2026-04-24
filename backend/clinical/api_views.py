"""API views for medical records/health records"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from users.models import PatientHealthRecord, PatientVitalLog
from users.api_serializers import PatientHealthRecordSerializer, PatientVitalLogSerializer
from clinical.models import Doctor, DoctorLeave
from rest_framework import serializers
from clinical.models import Specialization, Shift, DoctorSchedule

User = get_user_model()


class DoctorLeaveSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)

    class Meta:
        model = DoctorLeave
        fields = ['id', 'doctor', 'doctor_name', 'date', 'reason', 'approval_status', 'reviewed_by', 'reviewed_by_name', 'reviewed_at', 'review_notes', 'created_at']
        read_only_fields = ['id', 'doctor_name', 'reviewed_by_name', 'created_at']

    def get_doctor_name(self, obj):
        full_name = f"{obj.doctor.user.first_name} {obj.doctor.user.last_name}".strip()
        return full_name or obj.doctor.user.username or obj.doctor.user.email


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'icon', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['id', 'name', 'start_time', 'end_time', 'slot_duration']
        read_only_fields = ['id']


class DoctorScheduleSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    shift_name = serializers.CharField(source='shift.name', read_only=True)

    class Meta:
        model = DoctorSchedule
        fields = ['id', 'doctor', 'doctor_name', 'day', 'shift', 'shift_name', 'is_active']
        read_only_fields = ['id', 'doctor_name', 'shift_name']

    def get_doctor_name(self, obj):
        full_name = f"{obj.doctor.user.first_name} {obj.doctor.user.last_name}".strip()
        return full_name or obj.doctor.user.username or obj.doctor.user.email


class DoctorCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    specialization = serializers.PrimaryKeyRelatedField(queryset=Specialization.objects.filter(is_active=True), required=False, allow_null=True)
    consultation_fee = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, default=0)
    experience_years = serializers.IntegerField(required=False, default=0)
    phone = serializers.CharField(required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    is_available = serializers.BooleanField(required=False, default=True)

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError('Email already exists.')
        return normalized

    def create(self, validated_data):
        specialization = validated_data.pop('specialization', None)
        password = validated_data.pop('password')
        username = (validated_data.pop('username', '') or '').strip()
        email = validated_data.pop('email')
        if not username:
            base = email.split('@')[0] or 'doctor'
            username = base
            suffix = 1
            while User.objects.filter(username=username).exists():
                username = f'{base}{suffix}'
                suffix += 1

        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            first_name=validated_data.pop('first_name'),
            last_name=validated_data.pop('last_name'),
            role='DOCTOR',
            is_active=True,
        )
        doctor = Doctor.objects.create(
            user=user,
            specialization=specialization,
            consultation_fee=validated_data.get('consultation_fee', 0),
            experience_years=validated_data.get('experience_years', 0),
            phone=validated_data.get('phone', ''),
            bio=validated_data.get('bio', ''),
            is_available=validated_data.get('is_available', True),
        )
        return doctor


def _is_admin(request):
    return request.user.role == 'ADMIN'


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def specializations_list_create_api(request):
    if request.method == 'GET':
        items = Specialization.objects.all().order_by('name')
        serializer = SpecializationSerializer(items, many=True)
        return Response({'count': items.count(), 'results': serializer.data}, status=status.HTTP_200_OK)

    if not _is_admin(request):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = SpecializationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "PATCH", "DELETE"])
def specialization_detail_api(request, specialization_id):
    try:
        specialization = Specialization.objects.get(id=specialization_id)
    except Specialization.DoesNotExist:
        return Response({'detail': 'Specialization not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(SpecializationSerializer(specialization).data, status=status.HTTP_200_OK)

    if not _is_admin(request):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        specialization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = SpecializationSerializer(specialization, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def shifts_list_create_api(request):
    if request.method == 'GET':
        items = Shift.objects.all().order_by('start_time')
        serializer = ShiftSerializer(items, many=True)
        return Response({'count': items.count(), 'results': serializer.data}, status=status.HTTP_200_OK)

    if not _is_admin(request):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ShiftSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "PATCH", "DELETE"])
def shift_detail_api(request, shift_id):
    try:
        shift = Shift.objects.get(id=shift_id)
    except Shift.DoesNotExist:
        return Response({'detail': 'Shift not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ShiftSerializer(shift).data, status=status.HTTP_200_OK)

    if not _is_admin(request):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        shift.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ShiftSerializer(shift, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def schedules_list_create_api(request):
    if request.method == 'GET':
        schedules = DoctorSchedule.objects.select_related('doctor__user', 'shift').all().order_by('doctor__user__username', 'day')
        doctor_id = request.GET.get('doctor')
        if doctor_id:
            schedules = schedules.filter(doctor_id=doctor_id)
        serializer = DoctorScheduleSerializer(schedules, many=True)
        return Response({'count': schedules.count(), 'results': serializer.data}, status=status.HTTP_200_OK)

    if not _is_admin(request):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = DoctorScheduleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "PATCH", "DELETE"])
def schedule_detail_api(request, schedule_id):
    try:
        schedule = DoctorSchedule.objects.select_related('doctor__user', 'shift').get(id=schedule_id)
    except DoctorSchedule.DoesNotExist:
        return Response({'detail': 'Schedule not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(DoctorScheduleSerializer(schedule).data, status=status.HTTP_200_OK)

    if not _is_admin(request):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = DoctorScheduleSerializer(schedule, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def medical_records_list_api(request):
    """
    API endpoint to get medical records list with pagination.
    
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
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10
    
    records = PatientHealthRecord.objects.select_related('patient__user').all()

    if request.user.role == 'PATIENT':
        records = records.filter(patient__user=request.user)
    elif request.user.role not in ['DOCTOR', 'ADMIN', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    total_count = records.count()
    
    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_records = records[start_idx:end_idx]
    
    serializer = PatientHealthRecordSerializer(paginated_records, many=True)
    
    return Response(
        {
            'count': total_count,
            'next': f'/api/medical-records/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/medical-records/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def medical_record_detail_api(request, record_id):
    """
    API endpoint to get medical record detail.
    """
    try:
        record = PatientHealthRecord.objects.select_related('patient__user').get(id=record_id)

        if request.user.role == 'PATIENT' and record.patient.user_id != request.user.id:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        if request.user.role not in ['PATIENT', 'DOCTOR', 'ADMIN', 'RECEPTIONIST']:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PatientHealthRecordSerializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except PatientHealthRecord.DoesNotExist:
        return Response(
            {'detail': 'Medical record not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def medical_record_create_api(request):
    """
    API endpoint to create medical record.
    
    Expected POST data:
    {
        "patient": 1,
        "allergies": "...",
        "chronic_conditions": "...",
        "surgical_history": "...",
        "family_history": "...",
        "current_medications": "...",
        "immunization_notes": "...",
        "emergency_notes": "..."
    }
    """
    if request.user.role not in ['DOCTOR', 'ADMIN', 'RECEPTIONIST', 'NURSE']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        serializer = PatientHealthRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'detail': 'Validation error', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["PUT", "PATCH"])
def medical_record_update_api(request, record_id):
    """
    API endpoint to update medical record.
    """
    if request.user.role not in ['DOCTOR', 'ADMIN', 'RECEPTIONIST', 'NURSE']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        record = PatientHealthRecord.objects.get(id=record_id)
        partial = request.method == 'PATCH'
        serializer = PatientHealthRecordSerializer(record, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {'detail': 'Validation error', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
    except PatientHealthRecord.DoesNotExist:
        return Response(
            {'detail': 'Medical record not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def vital_logs_list_api(request):
    """
    API endpoint to get or create vital logs.

    GET query parameters:
    - page: Page number (default: 1)
    - page_size: Number of results per page (default: 10)
    - patient: Filter by patient ID (optional)
    """
    if request.method == 'POST':
        if request.user.role not in ['DOCTOR', 'ADMIN', 'RECEPTIONIST', 'NURSE']:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PatientVitalLogSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        log = serializer.save(recorded_by=request.user)
        return Response(PatientVitalLogSerializer(log).data, status=status.HTTP_201_CREATED)

    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10

    logs = PatientVitalLog.objects.select_related('patient__user', 'recorded_by').all()

    if request.user.role == 'PATIENT':
        logs = logs.filter(patient__user=request.user)
    elif request.user.role in ['DOCTOR', 'ADMIN', 'RECEPTIONIST', 'NURSE']:
        patient_id = request.GET.get('patient', '')
        if patient_id:
            logs = logs.filter(patient_id=patient_id)
    else:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    total_count = logs.count()

    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_logs = logs[start_idx:end_idx]

    serializer = PatientVitalLogSerializer(paginated_logs, many=True)

    return Response(
        {
            'count': total_count,
            'next': f'/api/vital-logs/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/vital-logs/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )

# ================== DOCTOR ENDPOINTS ==================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def doctors_list_api(request):
    """Get list of available doctors"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10
    
    from clinical.models import Doctor
    from appointments.api_serializers import DoctorSerializer
    
    # Filter by specialization if provided
    specialization_id = request.GET.get('specialization', '')
    if request.user.role in {'ADMIN', 'RECEPTIONIST'}:
        doctors = Doctor.objects.all().select_related('user', 'specialization')
    else:
        doctors = Doctor.objects.filter(is_available=True).select_related('user', 'specialization')
    
    if specialization_id:
        doctors = doctors.filter(specialization_id=specialization_id)
    
    total_count = doctors.count()
    
    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_doctors = doctors[start_idx:end_idx]
    
    serializer = DoctorSerializer(paginated_doctors, many=True, context={'request': request})
    
    return Response(
        {
            'count': total_count,
            'next': f'/api/doctors/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/doctors/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def doctor_create_api(request):
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = DoctorCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    doctor = serializer.save()
    return Response(DoctorSerializer(doctor, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def doctor_detail_api(request, doctor_id):
    """Get specific doctor detail"""
    try:
        from clinical.models import Doctor
        from appointments.api_serializers import DoctorSerializer
        from clinical.models import Specialization
        
        doctor = Doctor.objects.select_related('user', 'specialization').get(id=doctor_id)

        if request.method == 'DELETE':
            if request.user.role != 'ADMIN':
                return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
            doctor.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == 'PATCH':
            if request.user.role != 'ADMIN':
                return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

            data = request.data

            email = (data.get('email') or doctor.user.email or '').strip().lower()
            username = (data.get('username') or doctor.user.username or '').strip()
            first_name = (data.get('first_name') or doctor.user.first_name or '').strip()
            last_name = (data.get('last_name') or doctor.user.last_name or '').strip()

            if not email:
                return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
            if not first_name or not last_name:
                return Response({'detail': 'First name and last name are required.'}, status=status.HTTP_400_BAD_REQUEST)

            email_exists = User.objects.filter(email__iexact=email).exclude(id=doctor.user_id).exists()
            if email_exists:
                return Response({'detail': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

            if username:
                username_exists = User.objects.filter(username=username).exclude(id=doctor.user_id).exists()
                if username_exists:
                    return Response({'detail': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                base = email.split('@')[0] or 'doctor'
                username = base
                suffix = 1
                while User.objects.filter(username=username).exclude(id=doctor.user_id).exists():
                    username = f'{base}{suffix}'
                    suffix += 1

            specialization_id = data.get('specialization', None)
            specialization = doctor.specialization
            if specialization_id in ['', None]:
                specialization = None
            elif specialization_id is not None:
                try:
                    specialization = Specialization.objects.get(pk=int(specialization_id), is_active=True)
                except (TypeError, ValueError, Specialization.DoesNotExist):
                    return Response({'detail': 'Specialization not found.'}, status=status.HTTP_404_NOT_FOUND)

            doctor.user.email = email
            doctor.user.username = username
            doctor.user.first_name = first_name
            doctor.user.last_name = last_name
            doctor.user.save(update_fields=['email', 'username', 'first_name', 'last_name'])

            doctor.specialization = specialization
            if 'consultation_fee' in data:
                doctor.consultation_fee = data.get('consultation_fee') or 0
            if 'experience_years' in data:
                doctor.experience_years = data.get('experience_years') or 0
            if 'phone' in data:
                doctor.phone = (data.get('phone') or '').strip()
            if 'bio' in data:
                doctor.bio = (data.get('bio') or '').strip()
            if 'is_available' in data:
                doctor.is_available = bool(data.get('is_available'))
            doctor.save()

            return Response(DoctorSerializer(doctor, context={'request': request}).data, status=status.HTTP_200_OK)

        serializer = DoctorSerializer(doctor, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Doctor.DoesNotExist:
        return Response(
            {'detail': 'Doctor not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def doctor_leaves_api(request):
    """List/create leaves for the currently authenticated doctor."""
    if request.user.role != 'DOCTOR':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return Response({'detail': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        leaves = DoctorLeave.objects.filter(doctor=doctor).order_by('-date')
        serializer = DoctorLeaveSerializer(leaves, many=True)
        return Response({'results': serializer.data}, status=status.HTTP_200_OK)

    serializer = DoctorLeaveSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'detail': 'Validation error', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    date_value = serializer.validated_data['date']
    if date_value < timezone.localdate():
        return Response({'detail': 'Past leave dates are not allowed.'}, status=status.HTTP_400_BAD_REQUEST)

    if DoctorLeave.objects.filter(doctor=doctor, date=date_value).exists():
        return Response({'detail': 'Leave already exists on this date.'}, status=status.HTTP_400_BAD_REQUEST)

    leave = DoctorLeave.objects.create(
        doctor=doctor,
        date=date_value,
        reason=serializer.validated_data.get('reason', ''),
    )
    return Response(DoctorLeaveSerializer(leave).data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@require_http_methods(["PUT", "PATCH", "DELETE"])
def doctor_leave_detail_api(request, leave_id):
    """Update/delete a leave entry belonging to the authenticated doctor."""
    if request.user.role != 'DOCTOR':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return Response({'detail': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        leave = DoctorLeave.objects.get(id=leave_id, doctor=doctor)
    except DoctorLeave.DoesNotExist:
        return Response({'detail': 'Leave not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        leave.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    partial = request.method == 'PATCH'
    serializer = DoctorLeaveSerializer(leave, data=request.data, partial=partial)
    if not serializer.is_valid():
        return Response(
            {'detail': 'Validation error', 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_date = serializer.validated_data.get('date', leave.date)
    if new_date < timezone.localdate():
        return Response({'detail': 'Past leave dates are not allowed.'}, status=status.HTTP_400_BAD_REQUEST)

    duplicate = DoctorLeave.objects.filter(doctor=doctor, date=new_date).exclude(id=leave.id).exists()
    if duplicate:
        return Response({'detail': 'Leave already exists on this date.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def doctor_leaves_admin_api(request):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    leaves = DoctorLeave.objects.select_related('doctor__user', 'reviewed_by').all().order_by('-created_at')
    status_filter = request.GET.get('status', '').strip().upper()
    if status_filter in {'PENDING', 'APPROVED', 'REJECTED'}:
        leaves = leaves.filter(approval_status=status_filter)

    serializer = DoctorLeaveSerializer(leaves[:300], many=True)
    return Response({'count': leaves.count(), 'results': serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def doctor_leave_review_api(request, leave_id):
    if request.user.role != 'ADMIN':
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        leave = DoctorLeave.objects.select_related('doctor__user').get(pk=leave_id)
    except DoctorLeave.DoesNotExist:
        return Response({'detail': 'Leave not found.'}, status=status.HTTP_404_NOT_FOUND)

    action = (request.data.get('action') or '').strip().upper()
    notes = (request.data.get('notes') or '').strip()
    if action not in {'APPROVED', 'REJECTED'}:
        return Response({'detail': 'action must be APPROVED or REJECTED.'}, status=status.HTTP_400_BAD_REQUEST)

    if leave.approval_status != 'PENDING':
        return Response({'detail': f'Leave is already {leave.approval_status.lower()}.'}, status=status.HTTP_400_BAD_REQUEST)

    leave.approval_status = action
    leave.reviewed_by = request.user
    leave.reviewed_at = timezone.now()
    if notes:
        leave.review_notes = notes
    leave.save(update_fields=['approval_status', 'reviewed_by', 'reviewed_at', 'review_notes'])

    return Response(DoctorLeaveSerializer(leave).data, status=status.HTTP_200_OK)
