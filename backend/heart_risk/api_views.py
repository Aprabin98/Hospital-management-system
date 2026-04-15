"""API views for heart risk assessment endpoints"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.http import require_http_methods
from .models import HeartRiskAssessment
from .api_serializers import HeartRiskAssessmentSerializer
from .utils import calculate_heart_risk


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def heart_risk_assessments_list_api(request):
    """Get patient's heart risk assessments"""
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
    except (ValueError, TypeError):
        page = 1
        page_size = 10
    
    # Get current user's patient profile if exists
    from users.models import PatientProfile
    try:
        patient = PatientProfile.objects.get(user=request.user)
        assessments = HeartRiskAssessment.objects.filter(patient=patient).select_related('doctor')
    except PatientProfile.DoesNotExist:
        assessments = HeartRiskAssessment.objects.filter(assessed_by=request.user).select_related('doctor')
    
    total_count = assessments.count()
    
    # Simple pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_assessments = assessments[start_idx:end_idx]
    
    serializer = HeartRiskAssessmentSerializer(paginated_assessments, many=True)
    
    return Response(
        {
            'count': total_count,
            'next': f'/api/heart-risk/?page={page + 1}&page_size={page_size}' if end_idx < total_count else None,
            'previous': f'/api/heart-risk/?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def heart_risk_latest_api(request):
    """Get latest heart risk assessment for current patient"""
    try:
        from users.models import PatientProfile
        try:
            patient = PatientProfile.objects.get(user=request.user)
            assessment = HeartRiskAssessment.objects.filter(patient=patient).select_related('doctor').latest('created_at')
        except PatientProfile.DoesNotExist:
            assessment = HeartRiskAssessment.objects.filter(assessed_by=request.user).select_related('doctor').latest('created_at')
        
        serializer = HeartRiskAssessmentSerializer(assessment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except HeartRiskAssessment.DoesNotExist:
        return Response(
            {'detail': 'No heart risk assessment found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_http_methods(["GET"])
def heart_risk_assessment_detail_api(request, assessment_id):
    """Get specific heart risk assessment detail"""
    try:
        assessment = HeartRiskAssessment.objects.select_related('doctor', 'patient').get(id=assessment_id)

        if request.user.role == 'PATIENT':
            from users.models import PatientProfile
            patient = PatientProfile.objects.filter(user=request.user).first()
            if not patient or assessment.patient_id != patient.id:
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'DOCTOR':
            doctor = getattr(request.user, 'doctor_profile', None)
            if not doctor or assessment.doctor_id != doctor.id:
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role not in ['ADMIN', 'RECEPTIONIST']:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = HeartRiskAssessmentSerializer(assessment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except HeartRiskAssessment.DoesNotExist:
        return Response(
            {'detail': 'Heart risk assessment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'detail': f'Error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_http_methods(["POST"])
def heart_risk_assessment_create_api(request):
    """Create and save a new heart risk assessment."""
    required_fields = [
        'age',
        'sex',
        'systolic_bp',
        'diastolic_bp',
        'total_cholesterol',
        'fasting_blood_sugar',
        'bmi',
    ]
    for field in required_fields:
        if request.data.get(field) in [None, '']:
            return Response({'detail': f'{field} is required.'}, status=status.HTTP_400_BAD_REQUEST)

    from users.models import PatientProfile

    try:
        patient = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        inferred_name = (f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username or request.user.email)[:100]
        patient = PatientProfile.objects.create(
            user=request.user,
            full_name=inferred_name,
        )

    def _as_bool(value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {'true', '1', 'yes', 'on'}

    try:
        cleaned_data = {
            'age': int(request.data.get('age')),
            'sex': str(request.data.get('sex')).upper(),
            'systolic_bp': int(request.data.get('systolic_bp')),
            'diastolic_bp': int(request.data.get('diastolic_bp')),
            'total_cholesterol': int(request.data.get('total_cholesterol')),
            'fasting_blood_sugar': int(request.data.get('fasting_blood_sugar')),
            'bmi': float(request.data.get('bmi')),
            'smoker': _as_bool(request.data.get('smoker')),
            'diabetic': _as_bool(request.data.get('diabetic')),
            'family_history': _as_bool(request.data.get('family_history')),
            'chest_pain': _as_bool(request.data.get('chest_pain')),
            'sedentary_lifestyle': _as_bool(request.data.get('sedentary_lifestyle')),
        }
    except (TypeError, ValueError):
        return Response({'detail': 'Invalid numeric value provided.'}, status=status.HTTP_400_BAD_REQUEST)

    if cleaned_data['sex'] not in {'M', 'F', 'O'}:
        return Response({'detail': 'sex must be one of M, F, O.'}, status=status.HTTP_400_BAD_REQUEST)

    result = calculate_heart_risk(cleaned_data)

    doctor = None
    if request.user.role == 'DOCTOR':
        doctor = getattr(request.user, 'doctor_profile', None)

    assessment = HeartRiskAssessment.objects.create(
        patient=patient,
        assessed_by=request.user,
        doctor=doctor,
        age=cleaned_data['age'],
        sex=cleaned_data['sex'],
        systolic_bp=cleaned_data['systolic_bp'],
        diastolic_bp=cleaned_data['diastolic_bp'],
        total_cholesterol=cleaned_data['total_cholesterol'],
        fasting_blood_sugar=cleaned_data['fasting_blood_sugar'],
        bmi=cleaned_data['bmi'],
        smoker=cleaned_data['smoker'],
        diabetic=cleaned_data['diabetic'],
        family_history=cleaned_data['family_history'],
        chest_pain=cleaned_data['chest_pain'],
        sedentary_lifestyle=cleaned_data['sedentary_lifestyle'],
        risk_score=result['risk_score'],
        risk_level=result['risk_level'],
        summary=result['summary'],
        recommendations=result['recommendations'],
        metadata={
            'factors': result.get('factors', []),
            **result.get('metadata', {}),
        },
    )

    serializer = HeartRiskAssessmentSerializer(assessment)
    data = serializer.data
    data['saved'] = True
    return Response(data, status=status.HTTP_201_CREATED)
