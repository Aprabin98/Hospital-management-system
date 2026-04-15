"""Serializers for review-related API endpoints."""
from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    appointment_date = serializers.DateField(source='appointment.date', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'appointment',
            'appointment_date',
            'doctor',
            'doctor_name',
            'rating',
            'comment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'doctor', 'doctor_name', 'appointment_date', 'created_at', 'updated_at']
