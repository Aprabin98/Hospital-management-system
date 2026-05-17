import pytest
from rest_framework.test import APIClient

from clinical.models import Doctor, PatientVisit
from users.models import PatientAllergy, User


@pytest.mark.django_db
def test_patient_visit_stores_ai_suggestion_and_timeline():
    client = APIClient()
    doctor_user = User.objects.create_user(
        email='doctor.ai@example.com',
        username='doctor_ai',
        password='pass12345',
        role='DOCTOR',
        is_active=True,
    )
    Doctor.objects.create(user=doctor_user)
    patient_user = User.objects.create_user(
        email='patient.ai@example.com',
        username='patient_ai',
        password='pass12345',
        role='PATIENT',
        is_active=True,
    )
    patient = patient_user.patient_profile
    PatientAllergy.objects.create(patient=patient, allergen='Penicillin', severity='SEVERE')

    client.force_authenticate(doctor_user)
    response = client.post('/api/patient-visits/', {
        'patient': patient.id,
        'symptoms': 'fever and cough for three days',
        'prescribed_medicines': 'Penicillin',
        'vitals': {'temperature_c': 39},
    }, format='json')

    assert response.status_code == 201
    assert response.data['ai_risk_level'] == 'HIGH'
    assert 'CBC' in response.data['ai_recommended_tests']
    assert 'Allergy warning' in response.data['ai_red_flags']
    assert PatientVisit.objects.filter(patient=patient).count() == 1

    timeline = client.get(f'/api/patients/{patient.id}/timeline/')
    assert timeline.status_code == 200
    assert timeline.data['visits'][0]['id'] == response.data['id']
    assert timeline.data['active_allergies'][0]['allergen'] == 'Penicillin'
