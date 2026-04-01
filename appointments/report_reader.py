import re


def extract_text_from_file(uploaded_file):
    filename = (uploaded_file.name or '').lower()

    if filename.endswith('.txt'):
        uploaded_file.seek(0)
        return uploaded_file.read().decode('utf-8', errors='ignore')

    if filename.endswith('.pdf'):
        try:
            from pypdf import PdfReader

            uploaded_file.seek(0)
            reader = PdfReader(uploaded_file)
            parts = []
            for page in reader.pages:
                parts.append(page.extract_text() or '')
            return '\n'.join(parts).strip()
        except Exception:
            return ''

    uploaded_file.seek(0)
    return uploaded_file.read().decode('utf-8', errors='ignore')


def sanitize_text_for_storage(value):
    """Normalize text for legacy DB encodings (e.g., WIN1252) by replacing unsupported chars."""
    if value is None:
        return ''
    text = str(value)
    return text.encode('cp1252', errors='replace').decode('cp1252')


def sanitize_flags_for_storage(flags):
    safe_flags = []
    for item in flags or []:
        safe_item = {}
        for key, val in (item or {}).items():
            if isinstance(val, str):
                safe_item[key] = sanitize_text_for_storage(val)
            else:
                safe_item[key] = val
        safe_flags.append(safe_item)
    return safe_flags


def _find_numeric_value(text, aliases):
    alias_pattern = '|'.join(re.escape(alias) for alias in aliases)
    pattern = rf'(?:{alias_pattern})\s*[:=-]?\s*([0-9]+(?:\.[0-9]+)?)'
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _detect_report_type(text):
    normalized = (text or '').lower()
    if any(token in normalized for token in ['hemoglobin', 'wbc', 'platelet']):
        return 'CBC'
    if any(token in normalized for token in ['cholesterol', 'ldl', 'hdl', 'triglyceride']):
        return 'LIPID'
    if any(token in normalized for token in ['bilirubin', 'sgpt', 'sgot', 'alt', 'ast']):
        return 'LIVER'
    if any(token in normalized for token in ['creatinine', 'urea', 'bun', 'egfr']):
        return 'RENAL'
    if any(token in normalized for token in ['tsh', 't3', 't4']):
        return 'THYROID'
    if any(token in normalized for token in ['glucose', 'hba1c', 'fasting sugar']):
        return 'DIABETES'
    return 'GENERAL'


def build_personalized_guidance(report_type, risk_level, abnormal_flags):
    food_suggestions = [
        'Prefer freshly cooked meals and avoid highly processed packaged foods.',
        'Drink adequate water unless your doctor has advised fluid restriction.',
    ]
    exercise_suggestions = [
        'Aim for 20-30 minutes of light to moderate activity most days of the week.',
        'Include 5-10 minutes of stretching and breathing exercises daily.',
    ]
    health_tips = [
        'Track your symptoms and keep your follow-up appointments on time.',
        'Carry your latest reports when visiting your doctor.',
    ]

    if report_type == 'DIABETES':
        food_suggestions.extend([
            'Choose low-glycemic foods such as lentils, vegetables, and whole grains.',
            'Avoid sugary drinks and limit sweets and refined flour products.',
        ])
        exercise_suggestions.append('Add brisk walking for 30 minutes at least 5 days/week if medically fit.')
        health_tips.append('Monitor fasting/post-meal glucose regularly and review trend with your doctor.')

    if report_type == 'LIPID':
        food_suggestions.extend([
            'Increase fiber intake (oats, fruits, vegetables, legumes).',
            'Prefer healthy fats (nuts, seeds, fish) and avoid trans fats/deep-fried foods.',
        ])
        exercise_suggestions.append('Include cardio exercise at least 150 minutes per week as tolerated.')
        health_tips.append('Maintain weight control and recheck lipid profile as advised.')

    if report_type == 'CBC':
        food_suggestions.extend([
            'Include iron-rich foods such as spinach, beans, and lean proteins.',
            'Pair iron sources with vitamin C foods (orange, lemon, tomato) for better absorption.',
        ])
        health_tips.append('If fatigue, dizziness, or fever persists, seek clinician review promptly.')

    if report_type == 'RENAL':
        food_suggestions.extend([
            'Limit excess salt and processed snacks.',
            'Discuss potassium/protein limits with a nephrology professional if values are abnormal.',
        ])
        health_tips.append('Do not self-medicate painkillers frequently without medical advice.')

    if report_type == 'THYROID':
        health_tips.append('Take thyroid medications at consistent times if prescribed and monitor TSH trends.')

    if risk_level in ['HIGH', 'CRITICAL']:
        exercise_suggestions = [
            'Avoid intense workouts until your doctor confirms it is safe for your condition.',
            'Use gentle walking and breathing exercises unless advised otherwise.',
        ]
        health_tips.append('Book a priority consultation and share this analysis with a licensed doctor immediately.')

    if any((flag or {}).get('marker') == 'Glucose' for flag in (abnormal_flags or [])):
        food_suggestions.append('Use smaller meal portions and avoid late-night high-carb meals.')

    if any((flag or {}).get('marker') in {'LDL', 'Total Cholesterol', 'Triglycerides'} for flag in (abnormal_flags or [])):
        food_suggestions.append('Reduce red meat and full-fat dairy; prefer grilled/steamed meals.')

    return {
        'food_suggestions': food_suggestions[:5],
        'exercise_suggestions': exercise_suggestions[:5],
        'health_tips': health_tips[:6],
    }


def _build_detailed_summary_points(report_type, risk_level, abnormal_flags):
    marker_line = 'No major abnormal markers were detected from parsed values.'
    if abnormal_flags:
        marker_line = 'Abnormal markers detected: ' + ', '.join(
            f"{flag.get('marker')} ({flag.get('value')}, {str(flag.get('status')).replace('_', ' ')})"
            for flag in abnormal_flags[:5]
        )

    points = [
        f"Overall risk category is {risk_level} based on the available report values.",
        marker_line,
        'Possible causes include diet imbalance, low activity, stress, dehydration, infection, hormonal imbalance, or chronic disease progression.',
        'Likely effects can include fatigue, reduced concentration, poor recovery, and worsening organ stress if values remain uncontrolled.',
        'If uncontrolled, abnormalities may increase long-term risk of heart disease, kidney problems, stroke, nerve damage, or metabolic complications.',
        'Control plan should include timely physician consultation, repeat testing as advised, medication adherence, and lifestyle correction.',
        'Monitor symptoms daily and seek urgent care immediately if severe weakness, chest pain, breathlessness, confusion, or persistent vomiting occurs.',
        'Do not self-adjust prescription medicines without consulting a licensed doctor; carry this analysis and original report to follow-up visits.',
    ]

    if report_type == 'DIABETES':
        points.extend([
            'High glucose usually occurs due to insulin resistance, reduced insulin production, excess refined carbohydrates, poor sleep, stress hormones, or infection.',
            'Persistently high sugar can damage blood vessels and nerves, affecting eyes, kidneys, heart, feet, and wound healing over time.',
            'For better control, use portion control, avoid sugary drinks, reduce refined carbs, add fiber/protein in each meal, and stay physically active regularly.',
            'Track fasting and post-meal sugar readings, and discuss HbA1c trend targets with your doctor for long-term control.',
        ])
    elif report_type == 'LIPID':
        points.extend([
            'Abnormal lipid levels are commonly linked with high saturated fat intake, obesity, low activity, smoking, and genetic tendency.',
            'Uncontrolled cholesterol increases plaque formation and risk of heart attack, stroke, and peripheral artery disease.',
        ])
    elif report_type == 'CBC':
        points.extend([
            'CBC abnormalities may indicate anemia, infection, inflammation, bleeding tendency, or nutritional deficiency.',
            'Evaluate associated symptoms such as tiredness, fever, recurrent infections, bruising, or dizziness with your clinician.',
        ])

    unique_points = []
    for point in points:
        if point not in unique_points:
            unique_points.append(point)

    return unique_points[:12]


def analyze_report_text(text):
    content = (text or '').strip()
    if not content:
        fallback_points = [
            'No readable content was extracted from the uploaded report.',
            'The analysis confidence is low because numeric markers could not be parsed.',
            'Possible causes include scanned-image quality issues, encrypted PDF, or unsupported file formatting.',
            'Without parsed values, risk prediction can miss silent but clinically important abnormalities.',
            'Please upload a clearer report file, preferably text-based PDF or TXT format.',
            'Verify file size and ensure report pages are complete and not cropped.',
            'After re-upload, compare the analysis with your original report values for correctness.',
            'Always review final interpretation with a licensed doctor before treatment decisions.',
        ]
        return {
            'report_type': 'GENERAL',
            'risk_level': 'LOW',
            'ai_summary': '\n'.join(f"{idx}. {point}" for idx, point in enumerate(fallback_points, start=1)),
            'abnormal_flags': [],
            'recommendations': 'Upload a clearer PDF or a text report for better analysis.',
        }

    rules = [
        {'name': 'Hemoglobin', 'aliases': ['hemoglobin', 'hb'], 'low': 12.0, 'high': 17.5, 'critical_low': 8.0, 'critical_high': None},
        {'name': 'WBC', 'aliases': ['wbc', 'white blood cell'], 'low': 4000, 'high': 11000, 'critical_low': 2500, 'critical_high': 20000},
        {'name': 'Platelets', 'aliases': ['platelet', 'platelets'], 'low': 150000, 'high': 450000, 'critical_low': 80000, 'critical_high': 900000},
        {'name': 'Glucose', 'aliases': ['glucose', 'fasting sugar', 'blood sugar'], 'low': 70, 'high': 140, 'critical_low': 55, 'critical_high': 250},
        {'name': 'Creatinine', 'aliases': ['creatinine'], 'low': 0.6, 'high': 1.3, 'critical_low': None, 'critical_high': 2.5},
        {'name': 'TSH', 'aliases': ['tsh'], 'low': 0.4, 'high': 4.0, 'critical_low': 0.1, 'critical_high': 10.0},
        {'name': 'Total Cholesterol', 'aliases': ['total cholesterol', 'cholesterol'], 'low': 120, 'high': 200, 'critical_low': None, 'critical_high': 280},
        {'name': 'LDL', 'aliases': ['ldl'], 'low': 0, 'high': 130, 'critical_low': None, 'critical_high': 190},
        {'name': 'HDL', 'aliases': ['hdl'], 'low': 40, 'high': 90, 'critical_low': 30, 'critical_high': None},
        {'name': 'Triglycerides', 'aliases': ['triglyceride', 'triglycerides'], 'low': 0, 'high': 150, 'critical_low': None, 'critical_high': 500},
    ]

    abnormal_flags = []
    critical_count = 0

    for rule in rules:
        value = _find_numeric_value(content, rule['aliases'])
        if value is None:
            continue

        status = None
        if rule['critical_low'] is not None and value < rule['critical_low']:
            status = 'critical_low'
            critical_count += 1
        elif rule['critical_high'] is not None and value > rule['critical_high']:
            status = 'critical_high'
            critical_count += 1
        elif value < rule['low']:
            status = 'low'
        elif value > rule['high']:
            status = 'high'

        if status:
            abnormal_flags.append({
                'marker': rule['name'],
                'value': value,
                'status': status,
                'normal_range': f"{rule['low']} - {rule['high']}",
            })

    if critical_count > 0:
        risk_level = 'CRITICAL'
    elif len(abnormal_flags) >= 3:
        risk_level = 'HIGH'
    elif len(abnormal_flags) >= 1:
        risk_level = 'MODERATE'
    else:
        risk_level = 'LOW'

    report_type = _detect_report_type(content)

    summary_points = _build_detailed_summary_points(report_type, risk_level, abnormal_flags)
    summary = '\n'.join(f"{idx}. {point}" for idx, point in enumerate(summary_points, start=1))

    if not abnormal_flags:
        recommendations = 'Maintain routine follow-up and continue current care plan as advised by your doctor.'
    else:
        if risk_level == 'CRITICAL':
            recommendations = 'Seek urgent medical evaluation immediately and share this report with your doctor or emergency care.'
        elif risk_level == 'HIGH':
            recommendations = 'Book a doctor consultation within 24-48 hours for detailed interpretation and treatment planning.'
        else:
            recommendations = 'Schedule a follow-up consultation to review abnormal values and preventive actions.'

    return {
        'report_type': report_type,
        'risk_level': risk_level,
        'ai_summary': summary,
        'abnormal_flags': abnormal_flags,
        'recommendations': recommendations,
    }
