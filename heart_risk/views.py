import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from users.models import PatientProfile

from .forms import HeartRiskAssessmentForm
from .models import HeartRiskAssessment
from .utils import calculate_heart_risk


ALLOWED_ROLES = {'PATIENT', 'DOCTOR', 'RECEPTIONIST', 'ADMIN'}


@login_required
def assess_heart_risk(request):
    if request.user.role not in ALLOWED_ROLES:
        messages.error(request, 'Access denied for heart risk screening.')
        return redirect('users:dashboard')

    role = request.user.role
    latest_result = None

    if request.method == 'POST':
        form = HeartRiskAssessmentForm(request.POST, role=role)
        if form.is_valid():
            if role == 'PATIENT':
                patient = request.user.patient_profile
            else:
                patient_search = form.cleaned_data.get('patient_search', '').strip()
                if not patient_search:
                    messages.error(request, 'Please enter a patient name or ID.')
                    return render(
                        request,
                        'heart_risk/assess.html',
                        {
                            'form': form,
                            'latest_result': None,
                            'history': _history_for_user(request.user),
                        },
                    )
                
                patient = None
                try:
                    patient_id = int(patient_search)
                    patient = PatientProfile.objects.get(pk=patient_id)
                except (ValueError, PatientProfile.DoesNotExist):
                    patient = PatientProfile.objects.filter(
                        full_name__icontains=patient_search,
                        user__role='PATIENT'
                    ).first()
                
                if not patient:
                    messages.error(request, f'No patient found with name or ID: {patient_search}')
                    return render(
                        request,
                        'heart_risk/assess.html',
                        {
                            'form': form,
                            'latest_result': None,
                            'history': _history_for_user(request.user),
                        },
                    )

            result = calculate_heart_risk(form.cleaned_data)

            doctor = None
            if role == 'DOCTOR':
                doctor = getattr(request.user, 'doctor_profile', None)

            latest_result = HeartRiskAssessment.objects.create(
                patient=patient,
                assessed_by=request.user,
                doctor=doctor,
                age=form.cleaned_data['age'],
                sex=form.cleaned_data['sex'],
                systolic_bp=form.cleaned_data['systolic_bp'],
                diastolic_bp=form.cleaned_data['diastolic_bp'],
                total_cholesterol=form.cleaned_data['total_cholesterol'],
                fasting_blood_sugar=form.cleaned_data['fasting_blood_sugar'],
                bmi=form.cleaned_data['bmi'],
                smoker=form.cleaned_data.get('smoker', False),
                diabetic=form.cleaned_data.get('diabetic', False),
                family_history=form.cleaned_data.get('family_history', False),
                chest_pain=form.cleaned_data.get('chest_pain', False),
                sedentary_lifestyle=form.cleaned_data.get('sedentary_lifestyle', False),
                risk_score=result['risk_score'],
                risk_level=result['risk_level'],
                summary=result['summary'],
                recommendations=result['recommendations'],
                metadata={
                    'factors': result['factors'],
                    **result['metadata'],
                },
            )

            messages.success(request, 'Heart risk assessment completed and saved.')
            form = HeartRiskAssessmentForm(role=role)
        else:
            messages.error(request, 'Please correct the highlighted fields.')
    else:
        form = HeartRiskAssessmentForm(role=role)

    return render(
        request,
        'heart_risk/assess.html',
        {
            'form': form,
            'latest_result': latest_result,
            'history': _history_for_user(request.user),
        },
    )


def _history_for_user(user):
    queryset = HeartRiskAssessment.objects.select_related('patient__user', 'assessed_by')
    if user.role == 'PATIENT':
        return queryset.filter(patient=user.patient_profile)[:20]
    return queryset[:50]


@require_GET
def search_patients(request):
    """API endpoint to search patients by name or ID for autocomplete."""
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'results': []})

    patients = PatientProfile.objects.filter(
        user__role='PATIENT'
    ).select_related('user').order_by('full_name')

    try:
        patient_id = int(query)
        results = patients.filter(pk=patient_id)
    except ValueError:
        results = patients.filter(full_name__icontains=query) | patients.filter(user__email__icontains=query)

    results = results[:10]
    data = [
        {
            'id': p.pk,
            'name': f"{p.full_name} (ID: {p.pk})",
            'display': f"{p.full_name} - {p.user.email}",
        }
        for p in results
    ]
    return JsonResponse({'results': data})
