from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Appointment, WaitingList
from .no_show_predictor import PredictionEngine
from clinical.models import Doctor


def _can_manage_queue(user):
    return user.role in ['ADMIN', 'RECEPTIONIST']


@transaction.atomic
def promote_waiting_list(doctor, target_date, created_by=None):
    waiting = (
        WaitingList.objects.select_for_update()
        .filter(doctor=doctor, date=target_date, status='WAITING')
        .order_by('-priority', 'created_at')
        .first()
    )
    if not waiting:
        return None

    candidate_conflict = Appointment.objects.filter(
        doctor=doctor,
        date=target_date,
        status__in=['PENDING', 'CONFIRMED'],
    ).order_by('start_time').first()
    if not candidate_conflict:
        return None

    promoted = Appointment.objects.create(
        patient=waiting.patient,
        doctor=doctor,
        date=candidate_conflict.date,
        start_time=candidate_conflict.start_time,
        end_time=candidate_conflict.end_time,
        status='CONFIRMED',
        notes='Auto-promoted from waiting list.',
    )

    waiting.status = 'PROMOTED'
    waiting.notified_at = timezone.now()
    waiting.promoted_at = timezone.now()
    waiting.save(update_fields=['status', 'notified_at', 'promoted_at'])

    return promoted


@login_required
def no_show_risk_dashboard(request):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST', 'DOCTOR']:
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    upcoming = Appointment.objects.filter(
        date__gte=timezone.now().date(),
        status__in=['PENDING', 'CONFIRMED'],
    ).select_related('patient', 'doctor__user')[:100]

    payload = []
    for appointment in upcoming:
        prediction = PredictionEngine.predict_appointment(appointment)
        payload.append({
            'appointment_id': appointment.id,
            'patient': appointment.patient.full_name,
            'doctor': appointment.doctor.user.username,
            'date': appointment.date.isoformat(),
            'risk_level': prediction.risk_level,
            'probability': round(prediction.no_show_probability, 3),
        })

    return JsonResponse({'count': len(payload), 'items': payload})


@login_required
@require_POST
def set_no_show_outcome(request, appointment_id):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST', 'DOCTOR']:
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    appointment = get_object_or_404(Appointment, pk=appointment_id)
    outcome = request.POST.get('outcome', '').strip().lower()
    if outcome not in ['showed', 'no_show']:
        return JsonResponse({'detail': 'Invalid outcome.'}, status=400)

    prediction = PredictionEngine.predict_appointment(appointment)
    prediction.actually_no_showed = outcome == 'no_show'
    prediction.save(update_fields=['actually_no_showed', 'updated_at'])

    appointment.status = 'NO_SHOW' if prediction.actually_no_showed else 'COMPLETED'
    appointment.save(update_fields=['status', 'updated_at'])

    return JsonResponse({
        'appointment_id': appointment.id,
        'status': appointment.status,
        'risk_level': prediction.risk_level,
    })


@login_required
def waiting_list_queue(request):
    if not _can_manage_queue(request.user):
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    doctor_id = request.GET.get('doctor_id')
    qs = WaitingList.objects.filter(status='WAITING').select_related('patient', 'doctor__user')
    if doctor_id:
        qs = qs.filter(doctor_id=doctor_id)

    items = [
        {
            'id': row.id,
            'patient': row.patient.full_name,
            'doctor': row.doctor.user.username,
            'date': row.date.isoformat(),
            'priority': row.priority,
            'status': row.status,
        }
        for row in qs[:200]
    ]
    return JsonResponse({'count': len(items), 'items': items})


@login_required
@require_POST
def manual_promote_waiting(request, waiting_id):
    if not _can_manage_queue(request.user):
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    waiting = get_object_or_404(WaitingList, pk=waiting_id, status='WAITING')
    promoted = promote_waiting_list(waiting.doctor, waiting.date, created_by=request.user)
    if not promoted:
        return JsonResponse({'detail': 'No promotable slot available right now.'}, status=409)

    return JsonResponse({'promoted_appointment_id': promoted.id})


@login_required
@require_POST
def set_waiting_priority(request, waiting_id):
    if not _can_manage_queue(request.user):
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    waiting = get_object_or_404(WaitingList, pk=waiting_id)
    try:
        priority = int(request.POST.get('priority', waiting.priority))
    except ValueError:
        return JsonResponse({'detail': 'priority must be an integer.'}, status=400)

    waiting.priority = max(0, min(100, priority))
    waiting.save(update_fields=['priority'])
    return JsonResponse({'id': waiting.id, 'priority': waiting.priority})
