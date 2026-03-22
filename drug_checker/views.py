from itertools import combinations

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse

from .models import DrugInteraction, InteractionCheckLog


SEVERITY_RANK = {
    DrugInteraction.SEVERITY_MINOR: 1,
    DrugInteraction.SEVERITY_MODERATE: 2,
    DrugInteraction.SEVERITY_MAJOR: 3,
    DrugInteraction.SEVERITY_CONTRAINDICATED: 4,
}


def _normalize(name):
    return (name or '').strip().lower()


@login_required
def check_interactions(request):
    if request.user.role != 'DOCTOR':
        return JsonResponse({'detail': 'Access denied.'}, status=403)

    raw_medicines = request.GET.getlist('medicines')
    medicines = []
    for med in raw_medicines:
        normalized = _normalize(med)
        if normalized and normalized not in medicines:
            medicines.append(normalized)

    if len(medicines) < 2:
        return JsonResponse({
            'checked_count': len(medicines),
            'interactions_found': 0,
            'worst_severity': '',
            'interactions': [],
        })

    interactions = []

    for med_a, med_b in combinations(medicines, 2):
        match = DrugInteraction.objects.filter(
            is_active=True,
        ).filter(
            Q(drug_a_normalized=med_a, drug_b_normalized=med_b)
            | Q(drug_a_normalized=med_b, drug_b_normalized=med_a)
        ).first()

        if not match:
            # Fallback for partial naming differences.
            match = DrugInteraction.objects.filter(
                is_active=True,
            ).filter(
                (
                    Q(drug_a_normalized__icontains=med_a)
                    | Q(drug_b_normalized__icontains=med_a)
                )
                & (
                    Q(drug_a_normalized__icontains=med_b)
                    | Q(drug_b_normalized__icontains=med_b)
                )
            ).first()

        if match:
            interactions.append({
                'drug_a': med_a,
                'drug_b': med_b,
                'severity': match.severity,
                'description': match.description,
                'management': match.management,
            })

    worst_severity = ''
    if interactions:
        worst_severity = max(
            interactions,
            key=lambda item: SEVERITY_RANK.get(item['severity'], 0),
        )['severity']

    InteractionCheckLog.objects.create(
        checked_by=request.user,
        medicines=medicines,
        interactions_found=len(interactions),
        worst_severity=worst_severity,
    )

    return JsonResponse({
        'checked_count': len(medicines),
        'interactions_found': len(interactions),
        'worst_severity': worst_severity,
        'interactions': interactions,
    })
