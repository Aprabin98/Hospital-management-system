"""API views for appointments"""
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.http import FileResponse
from django.core.files.storage import default_storage
from django.utils import timezone
from appointments.models import (
    Appointment,
    MedicalReportAnalysis,
    TriageAssessment,
    Queue,
    NursingNote,
    NursingTask,
)
from .api_serializers import (
    AppointmentSerializer,
    MedicalReportAnalysisSerializer,
    TriageAssessmentSerializer,
    NursingNoteSerializer,
    NursingTaskSerializer,
)
from .utils import generate_available_slots, generate_qr_code, generate_appointment_pdf
from .triage import evaluate_triage
from audit.utils import log_audit_event
from .report_reader import (
    analyze_report_text,
    build_personalized_guidance,
    extract_text_from_file,
    sanitize_flags_for_storage,
    sanitize_text_for_storage,
)


ACTIVE_APPOINTMENT_STATUSES = ['PENDING', 'CONFIRMED']


def _appointment_time_range_conflicts(doctor, patient, booking_date, start_time_obj, end_time_obj, exclude_id=None):
    queryset = Appointment.objects.filter(
        date=booking_date,
        status__in=ACTIVE_APPOINTMENT_STATUSES,
    )

    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    overlapping = queryset.filter(
        Q(doctor=doctor) | Q(patient=patient)
    ).filter(
        start_time__lt=end_time_obj,
        end_time__gt=start_time_obj,
    ).select_related('patient__user', 'doctor__user')

    return overlapping.first()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def appointments_list_api(request):
    """
    API endpoint to get appointments list with pagination.
    
    Query parameters:
    - page: Page number (default: 1)
    - page_size: Number of results per page (default: 10)
    - status: Filter by status (optional)
    
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
    
    appointments = Appointment.objects.select_related('patient__user', 'doctor__user').all()

    if request.user.role == 'PATIENT':
        appointments = appointments.filter(patient__user=request.user)
    elif request.user.role == 'DOCTOR':
        if not hasattr(request.user, 'doctor_profile'):
            return Response({'detail': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        appointments = appointments.filter(doctor=request.user.doctor_profile)
    elif request.user.role not in ['ADMIN', 'RECEPTIONIST', 'NURSE']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        appointments = appointments.filter(status__iexact=status_filter)
    
    total_count = appointments.count()
    
    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_appointments = appointments[start_idx:end_idx]
    
    serializer = AppointmentSerializer(paginated_appointments, many=True)
    
    return Response(
        {
            'count': total_count,
            'next': f'/api/appointments/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/appointments/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def appointment_detail_api(request, appointment_id):
    """
    API endpoint to get appointment detail.
    """
    try:
        appointment = Appointment.objects.select_related('patient__user', 'doctor__user').get(id=appointment_id)

        if request.user.role == 'PATIENT' and appointment.patient.user_id != request.user.id:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        if request.user.role == 'DOCTOR':
            if not hasattr(request.user, 'doctor_profile'):
                return Response({'detail': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)
            if appointment.doctor_id != request.user.doctor_profile.id:
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        if request.user.role not in ['PATIENT', 'DOCTOR', 'ADMIN', 'RECEPTIONIST', 'NURSE']:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Appointment.DoesNotExist:
        return Response(
            {'detail': 'Appointment not found'},
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
def appointment_create_api(request):
    """
    API endpoint to create appointment.
    
    Expected POST data:
    {
        "patient": 1,
        "doctor": 1,
        "date": "2026-04-13",
        "start_time": "10:00",
        "end_time": "10:30",
        "status": "PENDING",
        "notes": "Some notes"
    }
    """
    from users.models import PatientProfile
    from clinical.models import Doctor

    allowed_roles = ['PATIENT', 'ADMIN', 'RECEPTIONIST']
    if request.user.role not in allowed_roles:
        return Response(
            {'detail': 'Only patients or front-desk/admin staff can create appointments.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    doctor_id = request.data.get('doctor')
    appointment_date = request.data.get('date')
    start_time = request.data.get('start_time')
    end_time = request.data.get('end_time')
    notes = request.data.get('notes', '')
    patient_id = request.data.get('patient')

    if not doctor_id or not appointment_date or not start_time:
        return Response(
            {'detail': 'doctor, date, and start_time are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        doctor = Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return Response({'detail': 'Doctor not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        booking_date = datetime.strptime(str(appointment_date), '%Y-%m-%d').date()
        start_time_obj = datetime.strptime(str(start_time), '%H:%M').time()
    except ValueError:
        return Response(
            {'detail': 'Invalid date or time format. Expected date=YYYY-MM-DD and start_time=HH:MM.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if booking_date < datetime.today().date():
        return Response({'detail': 'Cannot book an appointment in the past.'}, status=status.HTTP_400_BAD_REQUEST)

    # Patient users can only book for themselves. Front-desk/admin can provide patient id.
    if request.user.role == 'PATIENT':
        try:
            patient = PatientProfile.objects.get(user=request.user)
        except PatientProfile.DoesNotExist:
            return Response({'detail': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        if not patient_id:
            return Response({'detail': 'patient is required for this booking.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            patient = PatientProfile.objects.get(id=patient_id, user__role='PATIENT')
        except PatientProfile.DoesNotExist:
            return Response({'detail': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Day-level limit: max 2 active appointments for same patient.
    daily_count = Appointment.objects.filter(
        patient=patient,
        date=booking_date,
        status__in=['PENDING', 'CONFIRMED'],
    ).count()
    if daily_count >= 2:
        return Response(
            {'detail': 'Patient already has 2 appointments on this day.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    available_slots = generate_available_slots(doctor, booking_date)
    selected_slot = next((slot for slot in available_slots if slot['start'] == start_time_obj.strftime('%H:%M')), None)
    if not selected_slot:
        return Response({'detail': 'Selected slot is not available.'}, status=status.HTTP_400_BAD_REQUEST)

    end_time_obj = datetime.strptime(selected_slot['end'], '%H:%M').time()
    if end_time:
        try:
            provided_end = datetime.strptime(str(end_time), '%H:%M').time()
            end_time_obj = provided_end
        except ValueError:
            return Response({'detail': 'Invalid end_time format. Expected HH:MM.'}, status=status.HTTP_400_BAD_REQUEST)

    if end_time_obj <= start_time_obj:
        return Response({'detail': 'end_time must be later than start_time.'}, status=status.HTTP_400_BAD_REQUEST)

    conflict = _appointment_time_range_conflicts(doctor, patient, booking_date, start_time_obj, end_time_obj)
    if conflict:
        return Response(
            {
                'detail': 'Appointment overlaps with an existing booking.',
                'conflict': {
                    'appointment_id': conflict.id,
                    'doctor_id': conflict.doctor_id,
                    'patient_id': conflict.patient_id,
                    'date': conflict.date.isoformat(),
                    'start_time': conflict.start_time.strftime('%H:%M'),
                    'end_time': conflict.end_time.strftime('%H:%M'),
                },
            },
            status=status.HTTP_409_CONFLICT,
        )

    appointment = Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        date=booking_date,
        start_time=start_time_obj,
        end_time=end_time_obj,
        status='CONFIRMED',
        notes=notes,
    )

    # Keep API booking behavior aligned with template workflow.
    generate_qr_code(appointment)
    generate_appointment_pdf(appointment)
    appointment.save()

    serializer = AppointmentSerializer(appointment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["PUT", "PATCH"])
def appointment_update_api(request, appointment_id):
    """
    API endpoint to update appointment.
    """
    try:
        appointment = Appointment.objects.get(id=appointment_id)

        if request.user.role == 'PATIENT':
            if appointment.patient.user_id != request.user.id:
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
            # Patients can only cancel their own appointment via API.
            requested_status = (request.data.get('status') or '').upper()
            if requested_status and requested_status != 'CANCELLED':
                return Response({'detail': 'Patients can only cancel appointments.'}, status=status.HTTP_403_FORBIDDEN)

        elif request.user.role == 'DOCTOR':
            if not hasattr(request.user, 'doctor_profile'):
                return Response({'detail': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)
            if appointment.doctor_id != request.user.doctor_profile.id:
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        elif request.user.role not in ['ADMIN', 'RECEPTIONIST']:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        partial = request.method == 'PATCH'

        updated_doctor = appointment.doctor
        updated_patient = appointment.patient
        updated_date = appointment.date
        updated_start_time = appointment.start_time
        updated_end_time = appointment.end_time

        doctor_id = request.data.get('doctor')
        patient_id = request.data.get('patient')
        appointment_date = request.data.get('date')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')

        if doctor_id:
            from clinical.models import Doctor
            try:
                updated_doctor = Doctor.objects.get(id=doctor_id)
            except Doctor.DoesNotExist:
                return Response({'detail': 'Doctor not found.'}, status=status.HTTP_404_NOT_FOUND)

        if patient_id:
            from users.models import PatientProfile
            try:
                updated_patient = PatientProfile.objects.get(id=patient_id, user__role='PATIENT')
            except PatientProfile.DoesNotExist:
                return Response({'detail': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

        if appointment_date:
            try:
                updated_date = datetime.strptime(str(appointment_date), '%Y-%m-%d').date()
            except ValueError:
                return Response({'detail': 'Invalid date format. Expected YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if start_time:
            try:
                updated_start_time = datetime.strptime(str(start_time), '%H:%M').time()
            except ValueError:
                return Response({'detail': 'Invalid start_time format. Expected HH:MM.'}, status=status.HTTP_400_BAD_REQUEST)

        if end_time:
            try:
                updated_end_time = datetime.strptime(str(end_time), '%H:%M').time()
            except ValueError:
                return Response({'detail': 'Invalid end_time format. Expected HH:MM.'}, status=status.HTTP_400_BAD_REQUEST)

        if updated_end_time <= updated_start_time:
            return Response({'detail': 'end_time must be later than start_time.'}, status=status.HTTP_400_BAD_REQUEST)

        conflict = _appointment_time_range_conflicts(
            updated_doctor,
            updated_patient,
            updated_date,
            updated_start_time,
            updated_end_time,
            exclude_id=appointment.id,
        )
        if conflict:
            return Response(
                {
                    'detail': 'Appointment overlaps with an existing booking.',
                    'conflict': {
                        'appointment_id': conflict.id,
                        'doctor_id': conflict.doctor_id,
                        'patient_id': conflict.patient_id,
                        'date': conflict.date.isoformat(),
                        'start_time': conflict.start_time.strftime('%H:%M'),
                        'end_time': conflict.end_time.strftime('%H:%M'),
                    },
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer = AppointmentSerializer(appointment, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {'detail': 'Validation error', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Appointment.DoesNotExist:
        return Response(
            {'detail': 'Appointment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def appointments_available_slots_api(request):
    """Get doctor schedule and currently available slots for a given date."""
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return Response({'detail': 'doctor_id and date are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'detail': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    from clinical.models import Doctor, DoctorSchedule, DoctorLeave

    try:
        doctor = Doctor.objects.select_related('user').get(id=doctor_id)
    except Doctor.DoesNotExist:
        return Response({'detail': 'Doctor not found.'}, status=status.HTTP_404_NOT_FOUND)

    day_name = booking_date.strftime('%A')[:3].upper()
    full_day_name = booking_date.strftime('%A')
    schedule = DoctorSchedule.objects.select_related('shift').filter(
        doctor=doctor,
        is_active=True,
    ).filter(
        Q(day=day_name)
        | Q(day__iexact=full_day_name)
        | Q(day__istartswith=day_name)
    ).first()

    is_on_leave = DoctorLeave.objects.filter(doctor=doctor, date=booking_date).exists()
    slots = generate_available_slots(doctor, booking_date)

    return Response(
        {
            'doctor_id': doctor.id,
            'doctor_name': f"Dr. {doctor.user.first_name} {doctor.user.last_name}".strip(),
            'date': str(booking_date),
            'day': day_name,
            'is_on_leave': is_on_leave,
            'schedule': {
                'shift_name': schedule.shift.name if schedule else None,
                'start_time': schedule.shift.start_time.strftime('%H:%M') if schedule else None,
                'end_time': schedule.shift.end_time.strftime('%H:%M') if schedule else None,
                'slot_duration': schedule.shift.slot_duration if schedule else None,
            },
            'slots': [{'start': slot['start'], 'end': slot['end']} for slot in slots],
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def appointment_download_pdf_api(request, appointment_id):
    """Download appointment PDF for authorized users."""
    from users.models import PatientProfile

    try:
        appointment = Appointment.objects.select_related('patient', 'doctor__user').get(id=appointment_id)
    except Appointment.DoesNotExist:
        return Response({'detail': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role == 'PATIENT':
        try:
            profile = PatientProfile.objects.get(user=request.user)
        except PatientProfile.DoesNotExist:
            return Response({'detail': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)
        if appointment.patient_id != profile.id:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

    if request.user.role == 'DOCTOR' and hasattr(request.user, 'doctor_profile'):
        if appointment.doctor_id != request.user.doctor_profile.id:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

    if request.user.role not in ['PATIENT', 'DOCTOR', 'ADMIN', 'RECEPTIONIST', 'NURSE']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    pdf_missing = (
        not appointment.pdf_file
        or not appointment.pdf_file.name
        or not default_storage.exists(appointment.pdf_file.name)
    )

    if pdf_missing:
        generate_qr_code(appointment)
        generate_appointment_pdf(appointment)
        appointment.save(update_fields=['qr_code', 'pdf_file', 'updated_at'])

    if not appointment.pdf_file or not appointment.pdf_file.name:
        return Response({'detail': 'PDF not available.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    response = FileResponse(appointment.pdf_file.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="appointment_{appointment.id}.pdf"'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def report_reader_list_api(request):
    """Get AI report analysis history for current user/patient."""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10

    from users.models import PatientProfile
    try:
        patient = PatientProfile.objects.get(user=request.user)
        analyses = MedicalReportAnalysis.objects.filter(patient=patient).select_related('patient__user')
    except PatientProfile.DoesNotExist:
        analyses = MedicalReportAnalysis.objects.filter(created_by=request.user).select_related('patient__user')

    total_count = analyses.count()
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_analyses = analyses[start_idx:end_idx]

    serializer = MedicalReportAnalysisSerializer(paginated_analyses, many=True, context={'request': request})
    return Response(
        {
            'count': total_count,
            'next': f'/api/ai-report-reader/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/ai-report-reader/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def report_reader_create_api(request):
    """Upload a medical report file and generate AI analysis."""
    report_file = request.FILES.get('report_file')
    if not report_file:
        return Response({'detail': 'Please upload a report file.'}, status=status.HTTP_400_BAD_REQUEST)

    filename = (report_file.name or '').lower()
    if not filename.endswith(('.pdf', '.txt')):
        return Response({'detail': 'Only PDF and TXT files are supported.'}, status=status.HTTP_400_BAD_REQUEST)

    if report_file.size > 5 * 1024 * 1024:
        return Response({'detail': 'Report file must be smaller than 5 MB.'}, status=status.HTTP_400_BAD_REQUEST)

    from users.models import PatientProfile
    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        inferred_name = (f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username or request.user.email)[:100]
        patient = PatientProfile.objects.create(
            user=request.user,
            full_name=inferred_name,
        )

    analysis_title = (request.data.get('title') or '').strip()

    extracted_text = extract_text_from_file(report_file)
    report_result = analyze_report_text(extracted_text)

    analysis = MedicalReportAnalysis(
        patient=patient,
        title=analysis_title,
        report_file=report_file,
        created_by=request.user,
        extracted_text=sanitize_text_for_storage((extracted_text or '')[:20000]),
        report_type=report_result['report_type'],
        risk_level=report_result['risk_level'],
        ai_summary=sanitize_text_for_storage(report_result['ai_summary']),
        abnormal_flags=sanitize_flags_for_storage(report_result['abnormal_flags']),
        recommendations=sanitize_text_for_storage(report_result['recommendations']),
    )
    analysis.save()

    serializer = MedicalReportAnalysisSerializer(analysis, context={'request': request})
    data = serializer.data
    data['saved'] = True
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def report_reader_detail_api(request, analysis_id):
    """Get a single AI report analysis record."""
    try:
        analysis = MedicalReportAnalysis.objects.select_related('patient__user').get(pk=analysis_id)
    except MedicalReportAnalysis.DoesNotExist:
        return Response({'detail': 'Analysis not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role == 'PATIENT':
        from users.models import PatientProfile
        try:
            profile = PatientProfile.objects.get(user=request.user)
            if analysis.patient_id != profile.id:
                return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        except PatientProfile.DoesNotExist:
            return Response({'detail': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    guidance = build_personalized_guidance(
        analysis.report_type,
        analysis.risk_level,
        analysis.abnormal_flags,
    )
    summary_points = [
        line.strip()
        for line in (analysis.ai_summary or '').splitlines()
        if line.strip()
    ]
    disclaimer = (
        'This report is read and analyzed by trained AI models on real-world style data and may not always be fully accurate. '
        'Please show this analysis to a professional licensed doctor before making medical decisions.'
    )

    serializer = MedicalReportAnalysisSerializer(analysis, context={'request': request})
    data = serializer.data
    data['summary_points'] = summary_points
    data['guidance'] = guidance
    data['disclaimer'] = disclaimer
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def ai_triage_api(request):
    """List/create triage assessments with patient-scoped visibility."""
    from users.models import PatientProfile

    if request.method == 'GET':
        if request.user.role == 'PATIENT':
            try:
                patient = PatientProfile.objects.get(user=request.user)
            except PatientProfile.DoesNotExist:
                return Response({'detail': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)
            queryset = TriageAssessment.objects.filter(patient=patient).select_related('patient__user')
        elif request.user.role in ['DOCTOR', 'ADMIN', 'RECEPTIONIST', 'NURSE']:
            queryset = TriageAssessment.objects.select_related('patient__user')
        else:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TriageAssessmentSerializer(queryset[:100], many=True)
        return Response({'results': serializer.data}, status=status.HTTP_200_OK)

    if request.user.role != 'PATIENT':
        return Response({'detail': 'Only patients can create triage requests.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        return Response({'detail': 'Patient profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = TriageAssessmentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    triage_input = serializer.validated_data
    result = evaluate_triage(triage_input)

    triage = TriageAssessment.objects.create(
        patient=patient,
        symptoms=triage_input.get('symptoms', ''),
        duration_days=triage_input.get('duration_days', 1),
        pain_level=triage_input.get('pain_level', 0),
        has_fever=triage_input.get('has_fever', False),
        has_breathing_issue=triage_input.get('has_breathing_issue', False),
        has_chest_pain=triage_input.get('has_chest_pain', False),
        has_heavy_bleeding=triage_input.get('has_heavy_bleeding', False),
        had_fainting_episode=triage_input.get('had_fainting_episode', False),
        priority=result['priority'],
        priority_score=result['priority_score'],
        ai_summary=result['ai_summary'],
        recommended_action=result['recommended_action'],
        created_by=request.user,
    )

    return Response(TriageAssessmentSerializer(triage).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def nurse_dashboard_api(request):
    """Phase 3 nurse board: queue, triage and pending nursing workload."""
    if request.user.role not in ['NURSE', 'ADMIN', 'DOCTOR']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    today = timezone.localdate()

    queue_queryset = Queue.objects.select_related('patient__user', 'doctor__user').filter(
        status__in=['WAITING', 'CALLED', 'IN_CONSULTATION'],
    ).order_by('priority', 'queued_at')
    queue_items = queue_queryset[:120]

    triage_queryset = TriageAssessment.objects.select_related('patient__user').order_by('-created_at')
    triage_items = triage_queryset[:120]

    task_queryset = NursingTask.objects.select_related('patient__user', 'assigned_to').exclude(status='DONE').order_by('status', 'due_at', '-created_at')
    task_items = task_queryset[:120]

    return Response(
        {
            'kpis': {
                'active_queue_count': queue_queryset.count(),
                'high_priority_triage_count': triage_queryset.filter(priority__in=['P1', 'P2']).count(),
                'pending_tasks_count': task_queryset.count(),
                'today_appointments_count': Appointment.objects.filter(date=today).count(),
            },
            'queue': [
                {
                    'id': entry.id,
                    'patient_id': entry.patient_id,
                    'patient_name': entry.patient.full_name,
                    'doctor_name': f"Dr. {entry.doctor.user.first_name} {entry.doctor.user.last_name}".strip(),
                    'status': entry.status,
                    'priority': entry.priority,
                    'wait_time_minutes': entry.wait_time_minutes,
                }
                for entry in queue_items
            ],
            'triage': TriageAssessmentSerializer(triage_items, many=True).data,
            'tasks': NursingTaskSerializer(task_items, many=True).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST"])
def nursing_notes_api(request):
    if request.user.role not in ['NURSE', 'DOCTOR', 'ADMIN']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        queryset = NursingNote.objects.select_related('patient__user', 'nurse').all().order_by('-created_at')
        appointment_id = request.GET.get('appointment_id')
        patient_id = request.GET.get('patient_id')
        if appointment_id:
            queryset = queryset.filter(appointment_id=appointment_id)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        serializer = NursingNoteSerializer(queryset[:200], many=True)
        return Response({'count': queryset.count(), 'results': serializer.data}, status=status.HTTP_200_OK)

    serializer = NursingNoteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    appointment = serializer.validated_data['appointment']
    patient = serializer.validated_data['patient']
    if appointment.patient_id != patient.id:
        return Response({'detail': 'appointment and patient mismatch.'}, status=status.HTTP_400_BAD_REQUEST)

    note = serializer.save(nurse=request.user)
    return Response(NursingNoteSerializer(note).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET", "POST", "PATCH"])
def nursing_tasks_api(request):
    if request.user.role not in ['NURSE', 'DOCTOR', 'ADMIN']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        queryset = NursingTask.objects.select_related('patient__user', 'assigned_to', 'created_by').all().order_by('status', 'due_at', '-created_at')
        appointment_id = request.GET.get('appointment_id')
        patient_id = request.GET.get('patient_id')
        if appointment_id:
            queryset = queryset.filter(appointment_id=appointment_id)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        serializer = NursingTaskSerializer(queryset[:250], many=True)
        return Response({'count': queryset.count(), 'results': serializer.data}, status=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = NursingTaskSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        appointment = serializer.validated_data['appointment']
        patient = serializer.validated_data['patient']
        if appointment.patient_id != patient.id:
            return Response({'detail': 'appointment and patient mismatch.'}, status=status.HTTP_400_BAD_REQUEST)

        task = serializer.save(created_by=request.user)
        return Response(NursingTaskSerializer(task).data, status=status.HTTP_201_CREATED)

    task_id = request.data.get('id')
    if not task_id:
        return Response({'detail': 'id is required for task update.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        task = NursingTask.objects.get(pk=task_id)
    except NursingTask.DoesNotExist:
        return Response({'detail': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = NursingTaskSerializer(task, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response({'detail': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    updated = serializer.save()
    if updated.status == 'DONE' and not updated.completed_at:
        updated.completed_at = timezone.now()
        updated.save(update_fields=['completed_at'])
    elif updated.status != 'DONE' and updated.completed_at is not None:
        updated.completed_at = None
        updated.save(update_fields=['completed_at'])

    return Response(NursingTaskSerializer(updated).data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@require_http_methods(["PATCH"])
def triage_priority_update_api(request, triage_id):
    """Nurse/doctor/admin can update triage priority with audit trail."""
    if request.user.role not in ['NURSE', 'DOCTOR', 'ADMIN']:
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        triage = TriageAssessment.objects.select_related('patient__user').get(pk=triage_id)
    except TriageAssessment.DoesNotExist:
        return Response({'detail': 'Triage record not found.'}, status=status.HTTP_404_NOT_FOUND)

    new_priority = (request.data.get('priority') or '').strip().upper()
    valid_priority = {'P1', 'P2', 'P3', 'P4'}
    if new_priority not in valid_priority:
        return Response({'detail': 'priority must be one of P1, P2, P3, P4.'}, status=status.HTTP_400_BAD_REQUEST)

    old_priority = triage.priority
    triage.priority = new_priority
    triage.reviewed_by = request.user
    triage.reviewed_at = timezone.now()
    triage.save(update_fields=['priority', 'reviewed_by', 'reviewed_at'])

    log_audit_event(
        action='UPDATE',
        request=request,
        target=triage,
        description='Triage priority updated by clinical staff.',
        metadata={
            'triage_id': triage.id,
            'patient_id': triage.patient_id,
            'old_priority': old_priority,
            'new_priority': new_priority,
            'updated_by_role': request.user.role,
        },
    )

    return Response(TriageAssessmentSerializer(triage).data, status=status.HTTP_200_OK)
