"""Small rule-based patient-history assistant for defence-ready clinical support."""

RULES = [
    {
        'keywords': ['fever', 'cough', 'cold', 'sore throat'],
        'causes': ['Respiratory infection', 'Viral fever', 'Pneumonia if severe'],
        'tests': ['CBC', 'CRP', 'Chest X-Ray'],
        'red_flags': ['Shortness of breath', 'Oxygen saturation below 94%', 'High fever for more than 3 days'],
        'risk': 'MEDIUM',
    },
    {
        'keywords': ['chest pain', 'breathless', 'palpitation'],
        'causes': ['Cardiac cause', 'Acidity/gastritis', 'Respiratory cause'],
        'tests': ['ECG', 'Troponin', 'Lipid Profile'],
        'red_flags': ['Pain radiating to left arm', 'Sweating', 'Severe breathlessness'],
        'risk': 'HIGH',
    },
    {
        'keywords': ['frequent urination', 'thirst', 'weight loss', 'sugar'],
        'causes': ['Diabetes mellitus', 'Urinary tract infection'],
        'tests': ['Fasting Blood Sugar', 'HbA1c', 'Urine Routine'],
        'red_flags': ['Confusion', 'Vomiting', 'Very high blood sugar'],
        'risk': 'MEDIUM',
    },
    {
        'keywords': ['stomach pain', 'abdominal pain', 'vomiting', 'diarrhea'],
        'causes': ['Gastroenteritis', 'Gastritis', 'Appendicitis if localized severe pain'],
        'tests': ['CBC', 'Stool Test', 'Ultrasound Abdomen'],
        'red_flags': ['Severe localized pain', 'Blood in stool', 'Persistent vomiting'],
        'risk': 'MEDIUM',
    },
    {
        'keywords': ['headache', 'dizziness', 'blurred vision'],
        'causes': ['Migraine', 'Hypertension', 'Neurological cause if severe'],
        'tests': ['Blood Pressure Monitoring', 'CBC', 'CT Head if red flags'],
        'red_flags': ['Sudden worst headache', 'Weakness in limbs', 'Loss of consciousness'],
        'risk': 'MEDIUM',
    },
]


def _split_text(value):
    return [item.strip() for item in value.splitlines() if item.strip()]


def analyze_patient_visit(patient, symptoms='', medicines=''):
    text = f"{symptoms} {medicines}".lower()
    matched = [rule for rule in RULES if any(word in text for word in rule['keywords'])]
    if not matched:
        matched = [{
            'causes': ['Needs doctor assessment based on history and examination'],
            'tests': ['CBC', 'Basic Metabolic Panel'],
            'red_flags': ['Worsening symptoms', 'Severe pain', 'Fainting or breathing difficulty'],
            'risk': 'LOW',
        }]

    causes, tests, red_flags = [], [], []
    risk_rank = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
    risk = 'LOW'
    for rule in matched:
        causes.extend(rule['causes'])
        tests.extend(rule['tests'])
        red_flags.extend(rule['red_flags'])
        if risk_rank[rule['risk']] > risk_rank[risk]:
            risk = rule['risk']

    allergies = list(patient.allergies.filter(status='ACTIVE').values_list('allergen', flat=True))
    medicine_text = medicines.lower()
    allergy_warnings = [a for a in allergies if a and a.lower() in medicine_text]
    if allergy_warnings:
        risk = 'HIGH'

    recent_visits = patient.visits.order_by('-visit_date')[:5]
    repeated = sum(1 for visit in recent_visits if any(k in visit.symptoms.lower() for k in text.split()[:6]))
    if repeated >= 2 and risk == 'LOW':
        risk = 'MEDIUM'

    health_record = getattr(patient, 'health_record', None)
    history_bits = []
    if health_record:
        history_bits.extend(_split_text(health_record.chronic_conditions))
        history_bits.extend(_split_text(health_record.current_medications))

    summary = (
        f"Patient has {recent_visits.count()} recent visit(s). "
        f"Active allergies: {', '.join(allergies) if allergies else 'none recorded'}. "
        f"Known history: {', '.join(history_bits[:5]) if history_bits else 'not recorded'}."
    )

    return {
        'possible_causes': sorted(set(causes)),
        'recommended_tests': sorted(set(tests)),
        'risk_level': risk,
        'red_flags': sorted(set(red_flags)),
        'allergy_warnings': allergy_warnings,
        'summary': summary,
        'disclaimer': 'AI suggestions are decision support only. Final diagnosis must be made by a doctor.',
    }
