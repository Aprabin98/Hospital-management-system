"""Serializers for heart risk assessment API endpoints"""
from rest_framework import serializers
from .models import HeartRiskAssessment


class HeartRiskAssessmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True, allow_null=True)
    
    class Meta:
        model = HeartRiskAssessment
        fields = [
            'id',
            'patient',
            'patient_name',
            'doctor',
            'doctor_name',
            'age',
            'sex',
            'systolic_bp',
            'diastolic_bp',
            'total_cholesterol',
            'fasting_blood_sugar',
            'bmi',
            'smoker',
            'diabetic',
            'family_history',
            'chest_pain',
            'sedentary_lifestyle',
            'risk_score',
            'risk_level',
            'summary',
            'recommendations',
            'created_at',
        ]
        read_only_fields = ['id', 'risk_score', 'risk_level', 'created_at']
