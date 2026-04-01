from django import forms
from .models import Appointment, WaitingList, TriageAssessment, MedicalReportAnalysis
from clinical.models import Specialization, Doctor, DoctorLeave
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

    def __init__(self, *args, doctor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.doctor = doctor

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date < date.today():
            raise forms.ValidationError('Please select a future date.')

        if self.doctor and DoctorLeave.objects.filter(doctor=self.doctor, date=appointment_date).exists():
            raise forms.ValidationError('Doctor is on leave on this date. Please choose another date.')

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


class TriageAssessmentForm(forms.ModelForm):
    class Meta:
        model = TriageAssessment
        fields = [
            'symptoms',
            'duration_days',
            'pain_level',
            'has_fever',
            'has_breathing_issue',
            'has_chest_pain',
            'has_heavy_bleeding',
            'had_fainting_episode',
        ]
        widgets = {
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your symptoms, when they started, and how severe they are.'
            }),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'pain_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
        }

    def clean_symptoms(self):
        symptoms = (self.cleaned_data.get('symptoms') or '').strip()
        if len(symptoms) < 10:
            raise forms.ValidationError('Please provide more symptom details (at least 10 characters).')
        return symptoms


class MedicalReportUploadForm(forms.ModelForm):
    class Meta:
        model = MedicalReportAnalysis
        fields = ['title', 'report_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional title (e.g., CBC March 2026)'
            }),
            'report_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.txt'
            }),
        }

    def clean_report_file(self):
        report_file = self.cleaned_data.get('report_file')
        if not report_file:
            raise forms.ValidationError('Please upload a report file.')

        allowed = ('.pdf', '.txt')
        filename = (report_file.name or '').lower()
        if not filename.endswith(allowed):
            raise forms.ValidationError('Only PDF and TXT files are supported.')

        max_size = 5 * 1024 * 1024
        if report_file.size > max_size:
            raise forms.ValidationError('Report file must be smaller than 5 MB.')

        return report_file