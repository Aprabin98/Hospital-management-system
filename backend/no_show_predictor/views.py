from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from clinical.models import Doctor
from users.models import PatientProfile

from .models import NoShowPredictionLog
from .utils import calculate_no_show_risk


@login_required
def predict_no_show_risk(request):
    if request.user.role not in ['PATIENT', 'RECEPTIONIST', 'ADMIN', 'DOCTOR']:
        return JsonResponse({'error': 'Access denied.'}, status=403)

    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    patient_id = request.GET.get('patient_id')
    should_log = request.GET.get('log') == '1'

    if not doctor_id or not date_str:
        return JsonResponse({'error': 'doctor_id and date are required.'}, status=400)

    try:
        doctor = Doctor.objects.get(pk=doctor_id)
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found.'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    if request.user.role == 'PATIENT':
        patient = request.user.patient_profile
    else:
        if not patient_id:
            return JsonResponse({'error': 'patient_id is required for this role.'}, status=400)
        try:
            patient = PatientProfile.objects.get(pk=patient_id)
        except PatientProfile.DoesNotExist:
            return JsonResponse({'error': 'Patient not found.'}, status=404)

    prediction = calculate_no_show_risk(patient, doctor, appointment_date)

    if should_log:
        NoShowPredictionLog.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_date,
            risk_score=prediction['risk_score'],
            risk_level=prediction['risk_level'],
            factors=prediction['factors'],
            metadata=prediction['metadata'],
            created_by=request.user,
        )

    return JsonResponse(
        {
            'doctor_id': doctor.id,
            'patient_id': patient.id,
            'appointment_date': appointment_date.isoformat(),
            **prediction,
        }
    )
