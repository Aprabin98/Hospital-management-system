from django import forms
from .models import Room, RoomBed, RoomAssignment
from clinical.models import Doctor


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
