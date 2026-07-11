from itertools import combinations

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse

from .forms import DrugInteractionForm
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


@login_required
def manage_interactions(request):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('users:dashboard')

    if request.method == 'POST':
        form = DrugInteractionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Drug interaction added successfully.')
            return redirect('drug_checker:manage_interactions')
        messages.error(request, 'Please correct the form errors below.')
    else:
        form = DrugInteractionForm()

    interactions = DrugInteraction.objects.all().order_by('-created_at')
    return render(
        request,
        'drug_checker/manage_interactions.html',
        {
            'form': form,
            'interactions': interactions,
        },
    )


@login_required
def toggle_interaction_status(request, pk):
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('users:dashboard')

    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('drug_checker:manage_interactions')

    interaction = get_object_or_404(DrugInteraction, pk=pk)
    interaction.is_active = not interaction.is_active
    interaction.save(update_fields=['is_active'])

    state = 'activated' if interaction.is_active else 'deactivated'
    messages.success(request, f'Interaction {state}.')
    return redirect('drug_checker:manage_interactions')



#this is just a check  
