"""Serializers for room-related API endpoints"""
from rest_framework import serializers
from .models import Room, RoomBed, RoomAssignment, AdmissionRequest


class RoomBedSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    
    class Meta:
        model = RoomBed
        fields = ['id', 'room', 'room_number', 'bed_number', 'status']
        read_only_fields = ['id']


class RoomSerializer(serializers.ModelSerializer):
    beds = RoomBedSerializer(many=True, read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id',
            'room_number',
            'room_type',
            'floor',
            'capacity',
            'is_active',
            'occupied_beds',
            'available_beds',
            'notes',
            'beds',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'occupied_beds', 'available_beds', 'beds']


class RoomAssignmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True, allow_null=True)
    room_info = RoomSerializer(source='bed.room', read_only=True)
    bed_info = RoomBedSerializer(source='bed', read_only=True)
    
    class Meta:
        model = RoomAssignment
        fields = [
            'id',
            'patient',
            'patient_name',
            'bed',
            'bed_info',
            'room_info',
            'doctor',
            'doctor_name',
            'reason',
            'status',
            'admitted_at',
            'discharged_at',
            'discharge_notes',
        ]
        read_only_fields = ['id', 'admitted_at']


class AdmissionRequestSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True, allow_null=True)
    preferred_room_number = serializers.CharField(source='preferred_room.room_number', read_only=True, allow_null=True)
    
    class Meta:
        model = AdmissionRequest
        fields = [
            'id',
            'patient',
            'patient_name',
            'doctor',
            'doctor_name',
            'preferred_room',
            'preferred_room_number',
            'preferred_room_type',
            'reason',
            'status',
            'receptionist_notes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
