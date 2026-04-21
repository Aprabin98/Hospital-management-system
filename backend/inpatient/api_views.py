from django.db.models import Count
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit.utils import log_audit_event
from clinical.models import Doctor
from rooms.models import RoomAssignment
from users.models import PatientProfile

from .api_serializers import (
    DailyRoundSerializer,
    DischargePackageSerializer,
    InpatientStaySerializer,
    MedicationAdministrationRecordSerializer,
    ProcedureScheduleSerializer,
    ProgressNoteSerializer,
)
from .models import (
    DailyRound,
    DischargePackage,
    InpatientStay,
    MedicationAdministrationRecord,
    ProcedureSchedule,
    ProgressNote,
)


def _has_any_role(user, allowed_roles):
    return bool(user and user.is_authenticated and user.role in allowed_roles)


def _resolve_doctor_for_user(user):
    if not user or not user.is_authenticated:
        return None
    if user.role != 'DOCTOR':
        return None
    return Doctor.objects.filter(user=user).first()


def _get_stay_or_404(stay_id):
    try:
        return InpatientStay.objects.select_related('patient__user', 'attending_doctor__user', 'room_assignment__bed__room').get(id=stay_id)
    except InpatientStay.DoesNotExist:
        return None


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ipd_stays_api(request):
    if not _has_any_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        queryset = InpatientStay.objects.select_related(
            'patient__user', 'attending_doctor__user', 'room_assignment__bed__room'
        ).all()

        active_only = request.query_params.get('active')
        if active_only == 'true':
            queryset = queryset.filter(status='ADMITTED')

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter.upper())

        patient_name = request.query_params.get('patient_name')
        if patient_name:
            queryset = queryset.filter(patient__full_name__icontains=patient_name)

        doctor = _resolve_doctor_for_user(request.user)
        if doctor:
            queryset = queryset.filter(attending_doctor=doctor)

        serializer = InpatientStaySerializer(queryset, many=True)
        return Response({'count': len(serializer.data), 'results': serializer.data})

    data = request.data
    patient_id = data.get('patient_id')
    primary_diagnosis = (data.get('primary_diagnosis') or '').strip()

    if not patient_id or not primary_diagnosis:
        return Response(
            {'detail': 'patient_id and primary_diagnosis are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        patient = PatientProfile.objects.get(id=patient_id)
    except PatientProfile.DoesNotExist:
        return Response({'detail': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

    attending_doctor = None
    attending_doctor_id = data.get('attending_doctor_id')
    if attending_doctor_id:
        attending_doctor = Doctor.objects.filter(id=attending_doctor_id).first()

    room_assignment = None
    room_assignment_id = data.get('room_assignment_id')
    if room_assignment_id:
        room_assignment = RoomAssignment.objects.filter(id=room_assignment_id).first()

    stay = InpatientStay.objects.create(
        patient=patient,
        attending_doctor=attending_doctor,
        room_assignment=room_assignment,
        admission_request_id=data.get('admission_request_id') or None,
        admission_appointment_id=data.get('admission_appointment_id') or None,
        primary_diagnosis=primary_diagnosis,
        admission_reason=(data.get('admission_reason') or '').strip(),
        expected_discharge_date=data.get('expected_discharge_date') or None,
        admitted_by=request.user,
    )

    log_audit_event(
        action='IPD_STAY_CREATED',
        target=stay,
        description='Inpatient stay created',
        metadata={
            'patient_id': stay.patient_id,
            'doctor_id': stay.attending_doctor_id,
            'status': stay.status,
        },
        actor=request.user,
        request=request,
    )

    serializer = InpatientStaySerializer(stay)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def ipd_stay_detail_api(request, stay_id):
    if not _has_any_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    stay = _get_stay_or_404(stay_id)
    if not stay:
        return Response({'detail': 'Inpatient stay not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        payload = {
            'stay': InpatientStaySerializer(stay).data,
            'latest_round': DailyRoundSerializer(stay.daily_rounds.first()).data if stay.daily_rounds.exists() else None,
            'latest_progress_note': ProgressNoteSerializer(stay.progress_notes.first()).data if stay.progress_notes.exists() else None,
            'discharge_package': DischargePackageSerializer(stay.discharge_package).data if hasattr(stay, 'discharge_package') else None,
        }
        return Response(payload)

    if request.user.role not in ['ADMIN', 'DOCTOR']:
        return Response({'detail': 'Only admin/doctor can modify stay.'}, status=status.HTTP_403_FORBIDDEN)

    data = request.data
    updates = []

    if 'status' in data:
        next_status = str(data.get('status', '')).upper().strip()
        if next_status in {'ADMITTED', 'DISCHARGED', 'TRANSFERRED'}:
            stay.status = next_status
            if next_status == 'DISCHARGED' and not stay.actual_discharge_date:
                stay.actual_discharge_date = timezone.localdate()
            updates.append('status')

    if 'care_notes' in data:
        stay.care_notes = data.get('care_notes') or ''
        updates.append('care_notes')

    if 'expected_discharge_date' in data:
        stay.expected_discharge_date = data.get('expected_discharge_date') or None
        updates.append('expected_discharge_date')

    if updates:
        stay.save(update_fields=['status', 'care_notes', 'expected_discharge_date', 'actual_discharge_date', 'updated_at'])
        log_audit_event(
            action='IPD_STAY_UPDATED',
            target=stay,
            description='Inpatient stay updated',
            metadata={'updated_fields': updates},
            actor=request.user,
            request=request,
        )

    return Response(InpatientStaySerializer(stay).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ipd_progress_notes_api(request, stay_id):
    if not _has_any_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    stay = _get_stay_or_404(stay_id)
    if not stay:
        return Response({'detail': 'Inpatient stay not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        notes = stay.progress_notes.select_related('author').all()
        serializer = ProgressNoteSerializer(notes, many=True)
        return Response({'count': len(serializer.data), 'results': serializer.data})

    data = request.data
    note = ProgressNote.objects.create(
        inpatient_stay=stay,
        author=request.user,
        note_type=(data.get('note_type') or 'PROGRESS').upper(),
        clinical_findings=(data.get('clinical_findings') or '').strip(),
        assessment=(data.get('assessment') or '').strip(),
        plan=(data.get('plan') or '').strip(),
    )

    log_audit_event(
        action='IPD_PROGRESS_NOTE_CREATED',
        target=note,
        description='IPD progress note created',
        metadata={'stay_id': stay.id, 'note_type': note.note_type},
        actor=request.user,
        request=request,
    )

    return Response(ProgressNoteSerializer(note).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ipd_rounds_api(request, stay_id):
    if not _has_any_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    stay = _get_stay_or_404(stay_id)
    if not stay:
        return Response({'detail': 'Inpatient stay not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        rounds = stay.daily_rounds.select_related('round_assessor', 'signed_by').all()
        serializer = DailyRoundSerializer(rounds, many=True)
        return Response({'count': len(serializer.data), 'results': serializer.data})

    if request.user.role not in ['ADMIN', 'DOCTOR']:
        return Response({'detail': 'Only doctor/admin can create rounds.'}, status=status.HTTP_403_FORBIDDEN)

    data = request.data
    round_entry = DailyRound.objects.create(
        inpatient_stay=stay,
        round_date=data.get('round_date') or timezone.localdate(),
        round_assessor=request.user,
        round_notes=(data.get('round_notes') or '').strip(),
        vital_assessment=(data.get('vital_assessment') or '').strip(),
        current_status=(data.get('current_status') or '').strip(),
        orders=(data.get('orders') or '').strip(),
        is_signed=bool(data.get('is_signed')),
        signed_by=request.user if data.get('is_signed') else None,
        signed_at=timezone.now() if data.get('is_signed') else None,
    )

    log_audit_event(
        action='IPD_ROUND_CREATED',
        target=round_entry,
        description='IPD daily round created',
        metadata={'stay_id': stay.id, 'round_date': str(round_entry.round_date)},
        actor=request.user,
        request=request,
    )

    return Response(DailyRoundSerializer(round_entry).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ipd_discharge_api(request, stay_id):
    if not _has_any_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST', 'PATIENT']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    stay = _get_stay_or_404(stay_id)
    if not stay:
        return Response({'detail': 'Inpatient stay not found.'}, status=status.HTTP_404_NOT_FOUND)

    package = DischargePackage.objects.filter(inpatient_stay=stay).first()

    if request.method == 'GET':
        if not package:
            return Response({'detail': 'Discharge package not created yet.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(DischargePackageSerializer(package).data)

    data = request.data

    if request.user.role in ['ADMIN', 'DOCTOR']:
        required_fields = ['discharge_summary', 'discharge_instructions', 'follow_up_date']
        missing = [field for field in required_fields if not (data.get(field) or '').strip()]
        if missing and not package:
            return Response(
                {'detail': f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not package:
            package = DischargePackage.objects.create(
                inpatient_stay=stay,
                discharge_summary=(data.get('discharge_summary') or '').strip(),
                discharge_diagnoses=(data.get('discharge_diagnoses') or '').strip(),
                discharge_instructions=(data.get('discharge_instructions') or '').strip(),
                follow_up_date=data.get('follow_up_date'),
                follow_up_provider=(data.get('follow_up_provider') or '').strip(),
                follow_up_specialty=(data.get('follow_up_specialty') or '').strip(),
                nursing_clearance=bool(data.get('nursing_clearance')),
                pharmacy_clearance=bool(data.get('pharmacy_clearance')),
                billing_clearance=bool(data.get('billing_clearance')),
                doctor_signed_off_by=request.user,
                doctor_signed_off_at=timezone.now(),
            )
        else:
            package.discharge_summary = (data.get('discharge_summary', package.discharge_summary) or '').strip()
            package.discharge_diagnoses = (data.get('discharge_diagnoses', package.discharge_diagnoses) or '').strip()
            package.discharge_instructions = (data.get('discharge_instructions', package.discharge_instructions) or '').strip()
            package.follow_up_date = data.get('follow_up_date') or package.follow_up_date
            package.follow_up_provider = (data.get('follow_up_provider', package.follow_up_provider) or '').strip()
            package.follow_up_specialty = (data.get('follow_up_specialty', package.follow_up_specialty) or '').strip()
            package.nursing_clearance = bool(data.get('nursing_clearance', package.nursing_clearance))
            package.pharmacy_clearance = bool(data.get('pharmacy_clearance', package.pharmacy_clearance))
            package.billing_clearance = bool(data.get('billing_clearance', package.billing_clearance))

        if data.get('doctor_signoff'):
            package.doctor_signed_off_by = request.user
            package.doctor_signed_off_at = timezone.now()

        finalize = bool(data.get('finalize'))
        package.final_approved = finalize and package.checklist_complete
        package.save()

        if package.final_approved:
            stay.status = 'DISCHARGED'
            stay.actual_discharge_date = package.discharge_date
            stay.save(update_fields=['status', 'actual_discharge_date', 'updated_at'])

            if stay.room_assignment_id:
                assignment = stay.room_assignment
                assignment.status = 'DISCHARGED'
                assignment.discharged_at = timezone.now()
                assignment.discharge_notes = package.discharge_summary
                assignment.save(update_fields=['status', 'discharged_at', 'discharge_notes'])
                if assignment.bed_id:
                    assignment.bed.status = 'AVAILABLE'
                    assignment.bed.save(update_fields=['status'])

        log_audit_event(
            action='IPD_DISCHARGE_UPDATED',
            target=package,
            description='Discharge package created/updated',
            metadata={
                'stay_id': stay.id,
                'final_approved': package.final_approved,
            },
            actor=request.user,
            request=request,
        )

        return Response(DischargePackageSerializer(package).data)

    if request.user.role == 'PATIENT':
        if not package:
            return Response({'detail': 'Discharge package not available.'}, status=status.HTTP_404_NOT_FOUND)
        if stay.patient.user_id != request.user.id:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        package.patient_acknowledged_by = request.user
        package.patient_acknowledged_at = timezone.now()
        package.save(update_fields=['patient_acknowledged_by', 'patient_acknowledged_at', 'updated_at'])
        return Response(DischargePackageSerializer(package).data)

    return Response({'detail': 'Only doctor/admin can create discharge package.'}, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ipd_mar_api(request, stay_id):
    if not _has_any_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    stay = _get_stay_or_404(stay_id)
    if not stay:
        return Response({'detail': 'Inpatient stay not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        entries = stay.mar_entries.select_related('administered_by').all()
        serializer = MedicationAdministrationRecordSerializer(entries, many=True)
        return Response({'count': len(serializer.data), 'results': serializer.data})

    data = request.data
    entry = MedicationAdministrationRecord.objects.create(
        inpatient_stay=stay,
        prescription_item_id=data.get('prescription_item_id') or None,
        medication_name=(data.get('medication_name') or '').strip(),
        dose_given=(data.get('dose_given') or '').strip(),
        route=(data.get('route') or '').strip(),
        scheduled_datetime=data.get('scheduled_datetime') or timezone.now(),
        administered_datetime=data.get('administered_datetime') or None,
        status=(data.get('status') or 'SCHEDULED').upper(),
        administered_by=request.user if data.get('status', '').upper() in ['GIVEN', 'DELAYED'] else None,
        reason_not_given=(data.get('reason_not_given') or '').strip(),
        deviations=(data.get('deviations') or '').strip(),
        notes=(data.get('notes') or '').strip(),
    )

    log_audit_event(
        action='IPD_MAR_ENTRY_CREATED',
        target=entry,
        description='Medication administration record created',
        metadata={'stay_id': stay.id, 'status': entry.status},
        actor=request.user,
        request=request,
    )

    return Response(MedicationAdministrationRecordSerializer(entry).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ipd_procedures_api(request, stay_id):
    if not _has_any_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    stay = _get_stay_or_404(stay_id)
    if not stay:
        return Response({'detail': 'Inpatient stay not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        procedures = stay.procedures.select_related('surgeon__user').all()
        serializer = ProcedureScheduleSerializer(procedures, many=True)
        return Response({'count': len(serializer.data), 'results': serializer.data})

    if request.user.role not in ['ADMIN', 'DOCTOR']:
        return Response({'detail': 'Only doctor/admin can schedule procedures.'}, status=status.HTTP_403_FORBIDDEN)

    data = request.data
    procedure = ProcedureSchedule.objects.create(
        inpatient_stay=stay,
        procedure_name=(data.get('procedure_name') or '').strip(),
        scheduled_datetime=data.get('scheduled_datetime') or timezone.now(),
        ot_room_number=(data.get('ot_room_number') or '').strip(),
        surgeon_id=data.get('surgeon_id') or None,
        indication=(data.get('indication') or '').strip(),
        status=(data.get('status') or 'SCHEDULED').upper(),
        notes=(data.get('notes') or '').strip(),
    )

    log_audit_event(
        action='IPD_PROCEDURE_SCHEDULED',
        target=procedure,
        description='IPD procedure scheduled',
        metadata={'stay_id': stay.id, 'procedure_name': procedure.procedure_name},
        actor=request.user,
        request=request,
    )

    return Response(ProcedureScheduleSerializer(procedure).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ipd_dashboard_api(request):
    if not _has_any_role(request.user, ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST']):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    stays = InpatientStay.objects.all()
    today = timezone.localdate()

    metrics = {
        'stays': {
            'active': stays.filter(status='ADMITTED').count(),
            'discharged_today': stays.filter(status='DISCHARGED', actual_discharge_date=today).count(),
            'transferred': stays.filter(status='TRANSFERRED').count(),
        },
        'rounds': {
            'today': DailyRound.objects.filter(round_date=today).count(),
        },
        'discharge': {
            'pending_packages': stays.filter(status='ADMITTED').exclude(discharge_package__final_approved=True).count(),
            'finalized': DischargePackage.objects.filter(final_approved=True).count(),
        },
        'procedures': {
            'scheduled': ProcedureSchedule.objects.filter(status='SCHEDULED').count(),
            'completed_today': ProcedureSchedule.objects.filter(status='COMPLETED', actual_end_time__date=today).count(),
        },
        'mar': {
            'scheduled': MedicationAdministrationRecord.objects.filter(status='SCHEDULED').count(),
            'given_today': MedicationAdministrationRecord.objects.filter(status='GIVEN', administered_datetime__date=today).count(),
        },
        'occupancy': RoomAssignment.objects.filter(status='ADMITTED').aggregate(total=Count('id')),
    }

    return Response(metrics)
