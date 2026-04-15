from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Pharmacy, Prescription, PrescriptionRefill


@login_required
def refill_list(request):
    if request.user.role == 'PATIENT':
        qs = PrescriptionRefill.objects.filter(prescription__patient=request.user.patient_profile)
    elif request.user.role == 'DOCTOR':
        qs = PrescriptionRefill.objects.filter(prescription__doctor=request.user.doctor_profile)
    elif request.user.role in ['ADMIN', 'RECEPTIONIST']:
        qs = PrescriptionRefill.objects.all()
    else:
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    qs = qs.select_related('prescription__patient', 'prescription__doctor__user', 'pharmacy')
    items = [
        {
            'id': refill.id,
            'prescription_id': refill.prescription_id,
            'patient': refill.prescription.patient.full_name,
            'doctor': refill.prescription.doctor.user.username,
            'status': refill.status,
            'pharmacy': refill.pharmacy.name if refill.pharmacy else None,
            'requested_at': refill.requested_at.isoformat(),
        }
        for refill in qs[:200]
    ]
    return JsonResponse({'count': len(items), 'items': items})


@login_required
@require_POST
def request_refill(request, prescription_id):
    if request.user.role != 'PATIENT':
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    prescription = get_object_or_404(
        Prescription,
        pk=prescription_id,
        patient=request.user.patient_profile,
    )
    if not prescription.can_refill():
        return JsonResponse({'detail': 'No refill available for this prescription.'}, status=409)

    refill = PrescriptionRefill.objects.create(
        prescription=prescription,
        requested_by=request.user,
        reason=request.POST.get('reason', ''),
        is_urgent=request.POST.get('is_urgent') == '1',
    )
    return JsonResponse({'id': refill.id, 'status': refill.status}, status=201)


@login_required
@require_POST
def approve_refill(request, refill_id):
    if request.user.role != 'DOCTOR':
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    refill = get_object_or_404(
        PrescriptionRefill,
        pk=refill_id,
        prescription__doctor=request.user.doctor_profile,
    )
    if refill.status != 'REQUESTED':
        return JsonResponse({'detail': 'Only requested refills can be approved.'}, status=409)

    refill.status = 'APPROVED'
    refill.approved_by = request.user.doctor_profile
    refill.approved_at = timezone.now()
    refill.approval_notes = request.POST.get('approval_notes', '')
    refill.save(update_fields=['status', 'approved_by', 'approved_at', 'approval_notes'])

    return JsonResponse({'id': refill.id, 'status': refill.status})


@login_required
@require_POST
def pharmacy_fill_refill(request, refill_id):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    refill = get_object_or_404(PrescriptionRefill, pk=refill_id)
    if refill.status != 'APPROVED':
        return JsonResponse({'detail': 'Refill must be approved before filling.'}, status=409)

    pharmacy_id = request.POST.get('pharmacy_id')
    if not pharmacy_id:
        return JsonResponse({'detail': 'pharmacy_id is required.'}, status=400)

    pharmacy = get_object_or_404(Pharmacy, pk=pharmacy_id, is_active=True)

    refill.status = 'FILLED'
    refill.pharmacy = pharmacy
    refill.filled_at = timezone.now()
    refill.save(update_fields=['status', 'pharmacy', 'filled_at'])

    prescription = refill.prescription
    if prescription.can_refill():
        prescription.request_refill()

    return JsonResponse({'id': refill.id, 'status': refill.status, 'pharmacy': pharmacy.name})


@login_required
def pharmacy_list(request):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST', 'DOCTOR']:
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    pharmacies = Pharmacy.objects.filter(is_active=True).order_by('name')
    items = [
        {
            'id': p.id,
            'name': p.name,
            'location': p.location,
            'phone': p.phone,
            'email': p.email,
        }
        for p in pharmacies
    ]
    return JsonResponse({'count': len(items), 'items': items})
