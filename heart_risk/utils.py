from .ml_engine import predict_probability


def _clamp_percent(score):
    return max(1, min(99, int(round(score))))


def _calculate_rule_based(cleaned_data):
    """Fallback rule-based score when ML model is not available."""
    score = 8.0
    factors = []

    age = cleaned_data['age']
    systolic_bp = cleaned_data['systolic_bp']
    diastolic_bp = cleaned_data['diastolic_bp']
    cholesterol = cleaned_data['total_cholesterol']
    sugar = cleaned_data['fasting_blood_sugar']
    bmi = float(cleaned_data['bmi'])

    if age >= 60:
        score += 18
        factors.append('Age 60+ increases baseline cardiovascular risk.')
    elif age >= 45:
        score += 12
    elif age >= 35:
        score += 6

    if systolic_bp >= 160 or diastolic_bp >= 100:
        score += 20
        factors.append('Blood pressure is in a high-risk range.')
    elif systolic_bp >= 140 or diastolic_bp >= 90:
        score += 12
        factors.append('Blood pressure is above recommended control range.')
    elif systolic_bp >= 130 or diastolic_bp >= 85:
        score += 6

    if cholesterol >= 280:
        score += 18
        factors.append('Total cholesterol is very high.')
    elif cholesterol >= 240:
        score += 12
    elif cholesterol >= 200:
        score += 6

    if sugar >= 180:
        score += 16
        factors.append('Fasting blood sugar indicates poor glycemic control.')
    elif sugar >= 126:
        score += 10
    elif sugar >= 100:
        score += 4

    if bmi >= 35:
        score += 12
        factors.append('BMI in obesity range is a cardiovascular risk factor.')
    elif bmi >= 30:
        score += 8
    elif bmi >= 25:
        score += 4

    if cleaned_data.get('smoker'):
        score += 12
        factors.append('Smoking strongly increases heart attack risk.')

    if cleaned_data.get('diabetic'):
        score += 10
        factors.append('Diabetes increases long-term cardiovascular risk.')

    if cleaned_data.get('family_history'):
        score += 8
        factors.append('Family history adds hereditary risk burden.')

    if cleaned_data.get('chest_pain'):
        score += 15
        factors.append('Chest pain symptom requires prompt clinical follow-up.')

    if cleaned_data.get('sedentary_lifestyle'):
        score += 5

    risk_score = _clamp_percent(score)

    if risk_score >= 70:
        risk_level = 'HIGH'
        summary = 'High estimated heart attack risk.'
        recommendations = (
            'Urgent physician review recommended. Optimize blood pressure, sugar, and lipids. '
            'Consider ECG/lab workup and close follow-up.'
        )
    elif risk_score >= 40:
        risk_level = 'MEDIUM'
        summary = 'Moderate estimated heart attack risk.'
        recommendations = (
            'Lifestyle intervention and doctor follow-up advised. Improve diet, activity, and monitor vitals regularly.'
        )
    else:
        risk_level = 'LOW'
        summary = 'Low estimated heart attack risk at present.'
        recommendations = (
            'Maintain preventive lifestyle habits and repeat risk screening periodically.'
        )

    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'summary': summary,
        'recommendations': recommendations,
        'factors': factors,
        'metadata': {
            'method': 'rule_fallback',
            'inputs': {
                'age': age,
                'systolic_bp': systolic_bp,
                'diastolic_bp': diastolic_bp,
                'total_cholesterol': cholesterol,
                'fasting_blood_sugar': sugar,
                'bmi': bmi,
            }
        },
    }


def _build_ml_factors(cleaned_data):
    factors = []
    if cleaned_data.get('chest_pain'):
        factors.append('You reported chest pain or discomfort, which increases heart attack risk.')
    if int(cleaned_data.get('systolic_bp', 0)) >= 140:
        factors.append('Your top blood pressure number is high, which is a major heart risk factor.')
    if int(cleaned_data.get('total_cholesterol', 0)) >= 240:
        factors.append('Your cholesterol level is high, which can harm your heart and arteries.')
    if int(cleaned_data.get('fasting_blood_sugar', 0)) >= 120 or cleaned_data.get('diabetic'):
        factors.append('Your blood sugar is high or you have diabetes, which increases heart risk.')
    if cleaned_data.get('smoker'):
        factors.append('Smoking significantly increases your risk of heart attack and heart disease.')
    return factors


def calculate_heart_risk(cleaned_data):
    """ML-first risk calculation trained on online real data, with safe fallback."""
    try:
        probability, model_meta = predict_probability(cleaned_data)
        risk_score = _clamp_percent(probability * 100)

        if risk_score >= 70:
            risk_level = 'HIGH'
            summary = 'You have a HIGH risk for heart attack based on your health details.'
            recommendations = (
                'Please see a doctor immediately. They may want to do heart tests (like an ECG) '
                'and blood work. Work closely with your doctor to control blood pressure, cholesterol, '
                'and blood sugar. These changes can reduce your risk.'
            )
        elif risk_score >= 40:
            risk_level = 'MEDIUM'
            summary = 'You have a MEDIUM risk for heart attack based on your health details.'
            recommendations = (
                'Schedule a visit with your doctor soon to discuss your heart health. '
                'Ask about your blood pressure, cholesterol, and blood sugar levels. '
                'Making lifestyle changes like exercise, healthy eating, and stress management can help.'
            )
        else:
            risk_level = 'LOW'
            summary = 'You have a LOW risk for heart attack based on your health details.'
            recommendations = (
                'Keep doing what you are doing. Continue healthy habits like exercise, good diet, '
                'and managing stress. Have regular check-ups with your doctor to stay healthy.'
            )

        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'summary': summary,
            'recommendations': recommendations,
            'factors': _build_ml_factors(cleaned_data),
            'metadata': {
                'method': 'ml_trained_model',
                'probability': round(float(probability), 6),
                'model': {
                    'type': model_meta.get('model_type'),
                    'trained_at': model_meta.get('trained_at'),
                    'source': model_meta.get('source'),
                    'metrics': model_meta.get('metrics'),
                },
                'inputs': {
                    'age': cleaned_data.get('age'),
                    'sex': cleaned_data.get('sex'),
                    'systolic_bp': cleaned_data.get('systolic_bp'),
                    'diastolic_bp': cleaned_data.get('diastolic_bp'),
                    'total_cholesterol': cleaned_data.get('total_cholesterol'),
                    'fasting_blood_sugar': cleaned_data.get('fasting_blood_sugar'),
                    'bmi': float(cleaned_data.get('bmi')),
                },
            },
        }
    except Exception as exc:
        result = _calculate_rule_based(cleaned_data)
        result['summary'] = f"{result['summary']} (fallback: ML model unavailable)"
        result['metadata']['fallback_reason'] = str(exc)
        return result
