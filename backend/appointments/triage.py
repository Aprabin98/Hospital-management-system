import re


EMERGENCY_TERMS = {
    'unconscious',
    'seizure',
    'collapse',
    'stroke',
    'heart attack',
    'severe bleeding',
    'cannot breathe',
}

URGENT_TERMS = {
    'shortness of breath',
    'chest tightness',
    'vomiting blood',
    'high fever',
    'confusion',
    'dehydration',
}

MODERATE_TERMS = {
    'persistent cough',
    'dizziness',
    'headache',
    'abdominal pain',
    'fatigue',
    'fever',
}


def _contains_phrase(text, phrases):
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def evaluate_triage(payload):
    symptoms = (payload.get('symptoms') or '').strip()
    duration_days = int(payload.get('duration_days') or 0)
    pain_level = int(payload.get('pain_level') or 0)

    has_fever = bool(payload.get('has_fever'))
    has_breathing_issue = bool(payload.get('has_breathing_issue'))
    has_chest_pain = bool(payload.get('has_chest_pain'))
    has_heavy_bleeding = bool(payload.get('has_heavy_bleeding'))
    had_fainting_episode = bool(payload.get('had_fainting_episode'))

    score = 0
    reasons = []

    if has_breathing_issue:
        score += 40
        reasons.append('Breathing issue reported')
    if has_chest_pain:
        score += 35
        reasons.append('Chest pain reported')
    if has_heavy_bleeding:
        score += 45
        reasons.append('Heavy bleeding reported')
    if had_fainting_episode:
        score += 40
        reasons.append('Recent fainting episode reported')
    if has_fever:
        score += 15
        reasons.append('Fever reported')

    score += min(max(pain_level, 0), 10) * 4
    if pain_level >= 8:
        reasons.append('Severe pain level')

    if duration_days >= 7:
        score += 12
        reasons.append('Symptoms lasting more than a week')
    elif duration_days >= 3:
        score += 6

    cleaned = re.sub(r'\s+', ' ', symptoms.lower())
    if _contains_phrase(cleaned, EMERGENCY_TERMS):
        score += 45
        reasons.append('Emergency symptom keywords detected')
    elif _contains_phrase(cleaned, URGENT_TERMS):
        score += 25
        reasons.append('Urgent symptom keywords detected')
    elif _contains_phrase(cleaned, MODERATE_TERMS):
        score += 10
        reasons.append('Moderate symptom keywords detected')

    score = min(score, 100)

    if has_heavy_bleeding or had_fainting_episode or (has_chest_pain and has_breathing_issue):
        priority = 'P1'
    elif score >= 70:
        priority = 'P1'
    elif score >= 50:
        priority = 'P2'
    elif score >= 30:
        priority = 'P3'
    else:
        priority = 'P4'

    recommendations = {
        'P1': 'Seek emergency care immediately. Do not wait for routine appointment scheduling.',
        'P2': 'Visit urgent care or same-day doctor consultation as soon as possible.',
        'P3': 'Book doctor consultation within 24-48 hours and monitor symptom progression.',
        'P4': 'Routine consultation is appropriate. Continue home care and monitor symptoms.',
    }

    if not reasons:
        reasons.append('Limited risk indicators from current symptom input')

    return {
        'priority': priority,
        'priority_score': score,
        'ai_summary': '; '.join(reasons),
        'recommended_action': recommendations[priority],
    }
