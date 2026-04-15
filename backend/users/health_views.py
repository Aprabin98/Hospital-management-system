from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .forms import PatientHealthRecordForm, PatientVitalLogForm
from .models import PatientHealthRecord, PatientProfile, PatientVitalLog


@login_required
def health_record_detail(request, patient_id=None):
    if request.user.role == 'PATIENT':
        patient = request.user.patient_profile
    elif request.user.role in ['DOCTOR', 'ADMIN', 'LAB_TECHNICIAN', 'RECEPTIONIST']:
        if not patient_id:
            return JsonResponse({'detail': 'patient_id is required for this role.'}, status=400)
        patient = get_object_or_404(PatientProfile, pk=patient_id)
    else:
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    record, _ = PatientHealthRecord.objects.get_or_create(patient=patient)
    latest_vitals = list(
        PatientVitalLog.objects.filter(patient=patient).values(
            'blood_pressure',
            'pulse',
            'temperature_c',
            'respiratory_rate',
            'oxygen_saturation',
            'weight_kg',
            'height_cm',
            'recorded_at',
        )[:5]
    )

    return JsonResponse(
        {
            'patient_id': patient.id,
            'patient_name': patient.full_name,
            'record': {
                'allergies': record.allergies,
                'chronic_conditions': record.chronic_conditions,
                'surgical_history': record.surgical_history,
                'family_history': record.family_history,
                'current_medications': record.current_medications,
                'immunization_notes': record.immunization_notes,
                'emergency_notes': record.emergency_notes,
                'updated_at': record.updated_at.isoformat(),
            },
            'latest_vitals': latest_vitals,
        }
    )


@login_required
@require_POST
def upsert_health_record(request):
    if request.user.role != 'PATIENT':
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    record, _ = PatientHealthRecord.objects.get_or_create(patient=request.user.patient_profile)
    form = PatientHealthRecordForm(request.POST, instance=record)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    record = form.save(commit=False)
    record.updated_by = request.user
    record.save()

    return JsonResponse({'patient_id': request.user.patient_profile.id, 'updated': True})


@login_required
@require_POST
def add_vital_log(request, patient_id=None):
    if request.user.role == 'PATIENT':
        patient = request.user.patient_profile
    elif request.user.role in ['DOCTOR', 'LAB_TECHNICIAN', 'ADMIN', 'RECEPTIONIST']:
        if not patient_id:
            return JsonResponse({'detail': 'patient_id is required for this role.'}, status=400)
        patient = get_object_or_404(PatientProfile, pk=patient_id)
    else:
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    form = PatientVitalLogForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    vital = form.save(commit=False)
    vital.patient = patient
    vital.recorded_by = request.user
    vital.save()

    return JsonResponse({'id': vital.id, 'recorded_at': vital.recorded_at.isoformat()}, status=201)
