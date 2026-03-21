from django import forms
from .models import Appointment, WaitingList
from clinical.models import Specialization, Doctor
from datetime import date


class AppointmentStep1Form(forms.Form):
    """Step 1 - Select Specialization."""
    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.filter(is_active=True),
        empty_label="-- Select Specialization --",
        widget=forms.Select(attrs={'class': 'form-control form-select'})
    )


class AppointmentStep2Form(forms.Form):
    """Step 2 - Select Doctor."""
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.none(),
        empty_label="-- Select Doctor --",
        widget=forms.Select(attrs={'class': 'form-control form-select'})
    )

    def __init__(self, *args, specialization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if specialization:
            self.fields['doctor'].queryset = Doctor.objects.filter(
                specialization=specialization,
                is_available=True
            ).select_related('user')


class AppointmentStep3Form(forms.Form):
    """Step 3 - Select Date."""
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': str(date.today())
        })
    )

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date < date.today():
            raise forms.ValidationError('Please select a future date.')
        return appointment_date


class AppointmentStep4Form(forms.Form):
    """Step 4 - Select Time Slot."""
    slot = forms.CharField(
        widget=forms.HiddenInput()
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any notes for the doctor? (optional)'
        })
    )


class AppointmentCancelForm(forms.Form):
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for cancellation (optional)'
        })
    )


class WaitingListForm(forms.ModelForm):
    class Meta:
        model = WaitingList
        fields = ['doctor', 'date']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }