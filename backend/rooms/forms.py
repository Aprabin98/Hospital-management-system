from django import forms
from .models import AdmissionRequest, Room, RoomBed, RoomAssignment, RoomTransfer
from clinical.models import Doctor
from users.models import PatientProfile


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'floor', 'capacity', 'is_active', 'notes']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'room_type': forms.Select(attrs={'class': 'form-control'}),
            'floor': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class RoomBedForm(forms.ModelForm):
    class Meta:
        model = RoomBed
        fields = ['bed_number', 'status']
        widgets = {
            'bed_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class RoomAssignmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.select_related('user').all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = RoomAssignment
        fields = ['patient', 'bed', 'doctor', 'reason']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'bed': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bed'].queryset = RoomBed.objects.filter(status='AVAILABLE', room__is_active=True).select_related('room')


class RoomDischargeForm(forms.Form):
    discharge_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Discharge summary or notes'})
    )


class DoctorAdmissionRequestForm(forms.ModelForm):
    class Meta:
        model = AdmissionRequest
        fields = ['patient', 'preferred_room_type', 'reason']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'preferred_room_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reason for admission request'}),
        }

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        self.fields['patient'].queryset = PatientProfile.objects.none()

        if doctor is not None:
            from appointments.models import Appointment

            patient_ids = Appointment.objects.filter(
                doctor=doctor
            ).values_list('patient_id', flat=True).distinct()

            self.fields['patient'].queryset = PatientProfile.objects.filter(
                id__in=patient_ids
            ).select_related('user').order_by('full_name')


class RoomTransferForm(forms.ModelForm):
    """Form for doctor to transfer patient to a different room"""
    to_room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'transfer_room'}),
        label='Transfer to Room'
    )
    to_bed = forms.ModelChoiceField(
        queryset=RoomBed.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'transfer_bed'}),
        label='Transfer to Bed',
        required=True
    )
    
    class Meta:
        model = RoomTransfer
        fields = ['reason', 'notes']
        widgets = {
            'reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Reason for transfer (e.g., requires ICU, better isolation, patient preference)',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about the transfer'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only available beds in the to_bed field
        self.fields['to_bed'].queryset = RoomBed.objects.filter(
            status='AVAILABLE',
            room__is_active=True
        ).select_related('room')

