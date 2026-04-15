from datetime import date

from appointments.models import Appointment


def _to_int_score(value):
    return max(0, min(99, int(round(value))))


def calculate_no_show_risk(patient, doctor, appointment_date):
    """Heuristic no-show risk scoring used as phase-3 baseline model."""
    factors = []
    score = 20.0

    total_history = Appointment.objects.filter(
        patient=patient,
        status__in=['CANCELLED', 'COMPLETED', 'CONFIRMED'],
    ).count()
    cancelled_count = Appointment.objects.filter(
        patient=patient,
        status='CANCELLED',
    ).count()
    missed_confirmed_count = Appointment.objects.filter(
        patient=patient,
        status='CONFIRMED',
        date__lt=date.today(),
    ).count()

    risky_history = cancelled_count + missed_confirmed_count
    if total_history > 0:
        historical_risk_ratio = risky_history / float(total_history)
        score += historical_risk_ratio * 45.0
        if historical_risk_ratio >= 0.50:
            factors.append('Patient has high history of cancellations or missed visits.')
        elif historical_risk_ratio >= 0.20:
            factors.append('Patient has moderate history of cancellations/missed visits.')
    else:
        score += 8.0
        factors.append('No prior appointment history available; confidence is lower.')

    patient_profile_missing = not patient.phone or not patient.address
    if patient_profile_missing:
        score += 8.0
        factors.append('Patient profile contact/address is incomplete.')

    doctor_day_load = Appointment.objects.filter(
        doctor=doctor,
        date=appointment_date,
        status__in=['PENDING', 'CONFIRMED'],
    ).count()
    if doctor_day_load >= 14:
        score += 10.0
        factors.append('Doctor has a heavy schedule on the selected day.')
    elif doctor_day_load >= 8:
        score += 5.0

    day_delta = (appointment_date - date.today()).days
    if day_delta <= 1:
        score += 7.0
        factors.append('Very short lead time before appointment date.')
    elif day_delta >= 21:
        score += 4.0

    if appointment_date.weekday() in (5, 6):
        score += 5.0
        factors.append('Weekend appointments have slightly higher no-show behavior.')

    risk_score = _to_int_score(score)
    if risk_score >= 70:
        risk_level = 'HIGH'
    elif risk_score >= 40:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'

    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'factors': factors,
        'metadata': {
            'total_history': total_history,
            'cancelled_count': cancelled_count,
            'missed_confirmed_count': missed_confirmed_count,
            'doctor_day_load': doctor_day_load,
        },
    }
