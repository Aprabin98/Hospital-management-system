from django import forms
from .models import Prescription, PrescriptionItem


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['notes', 'advice', 'follow_up_date']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Diagnosis or general notes...'
            }),
            'advice': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "Doctor's advice to patient..."
            }),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }


class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = [
            'medicine_name', 'dosage', 'frequency',
            'duration', 'timing', 'instructions'
        ]
        widgets = {
            'medicine_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Medicine name'
            }),
            'dosage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 500mg'
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 5 days'
            }),
            'timing': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'instructions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Special instructions (optional)'
            }),
        }


# Formset for multiple medicines
PrescriptionItemFormSet = forms.inlineformset_factory(
    Prescription,
    PrescriptionItem,
    form=PrescriptionItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)