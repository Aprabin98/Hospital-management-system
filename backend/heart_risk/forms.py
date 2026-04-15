from django import forms

from users.models import PatientProfile

from .models import HeartRiskAssessment


class HeartRiskAssessmentForm(forms.Form):
    patient_search = forms.CharField(
        max_length=255,
        required=False,
        label='Search Patient by Name or ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type patient name or ID...',
            'autocomplete': 'off',
            'id': 'patient_search_input',
        }),
    )

    age = forms.IntegerField(min_value=1, max_value=120, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    sex = forms.ChoiceField(choices=HeartRiskAssessment.SEX_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    systolic_bp = forms.IntegerField(min_value=70, max_value=260, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    diastolic_bp = forms.IntegerField(min_value=40, max_value=180, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    total_cholesterol = forms.IntegerField(min_value=80, max_value=500, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    fasting_blood_sugar = forms.IntegerField(min_value=50, max_value=500, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    bmi = forms.DecimalField(min_value=10, max_value=60, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}))

    smoker = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    diabetic = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    family_history = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    chest_pain = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    sedentary_lifestyle = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def __init__(self, *args, **kwargs):
        role = kwargs.pop('role', None)
        super().__init__(*args, **kwargs)

        if role == 'PATIENT':
            self.fields['patient_search'].widget = forms.HiddenInput()
