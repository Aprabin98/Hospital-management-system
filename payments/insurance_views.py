from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import InsuranceVerificationActionForm, InsuranceVerificationForm
from .models import InsuranceVerification


@login_required
def insurance_list(request):
    if request.user.role == 'PATIENT':
        qs = InsuranceVerification.objects.filter(patient=request.user.patient_profile)
    elif request.user.role in ['ADMIN', 'RECEPTIONIST']:
        qs = InsuranceVerification.objects.all().select_related('patient__user', 'verified_by')
    else:
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    for row in qs:
        row.mark_expired_if_needed()

    items = [
        {
            'id': item.id,
            'patient': item.patient.full_name,
            'provider_name': item.provider_name,
            'policy_number': item.policy_number,
            'coverage_percent': item.coverage_percent,
            'status': item.status,
            'valid_until': item.valid_until.isoformat() if item.valid_until else None,
        }
        for item in qs[:200]
    ]
    return JsonResponse({'count': len(items), 'items': items})


@login_required
@require_POST
def insurance_create(request):
    if request.user.role != 'PATIENT':
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    form = InsuranceVerificationForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    insurance = form.save(commit=False)
    insurance.patient = request.user.patient_profile
    insurance.status = 'PENDING'
    insurance.save()

    return JsonResponse({'id': insurance.id, 'status': insurance.status}, status=201)


@login_required
@require_POST
def insurance_verify(request, insurance_id):
    if request.user.role not in ['ADMIN', 'RECEPTIONIST']:
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    insurance = get_object_or_404(InsuranceVerification, pk=insurance_id)
    form = InsuranceVerificationActionForm(request.POST, instance=insurance)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    insurance = form.save(commit=False)
    insurance.verified_by = request.user
    insurance.verified_at = timezone.now()

    if insurance.valid_until and insurance.valid_until < timezone.now().date() and insurance.status == 'VERIFIED':
        insurance.status = 'EXPIRED'

    insurance.save()
    return JsonResponse({'id': insurance.id, 'status': insurance.status})
