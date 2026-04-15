from django import forms
from .models import TestTemplate, TestField, TestSchedule, TestBooking, TestResult, TestResultItem
from datetime import date


class TestTemplateForm(forms.ModelForm):
    class Meta:
        model = TestTemplate
        fields = ['name', 'description', 'preparation', 'price', 'duration_minutes', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Blood Sugar Test'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preparation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g. Fast for 8 hours before test'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TestFieldForm(forms.ModelForm):
    class Meta:
        model = TestField
        fields = [
            'field_name', 'unit', 'normal_min', 'normal_max',
            'critical_min', 'critical_max', 'normal_text',
            'field_type', 'is_required', 'order'
        ]
        widgets = {
            'field_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Fasting Blood Sugar'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. mg/dL'}),
            'normal_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min normal value'}),
            'normal_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max normal value'}),
            'critical_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Critical low threshold'}),
            'critical_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Critical high threshold'}),
            'normal_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'For text fields e.g. Negative'}),
            'field_type': forms.Select(attrs={'class': 'form-control form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TestScheduleForm(forms.ModelForm):
    class Meta:
        model = TestSchedule
        fields = ['day', 'start_time', 'end_time', 'max_bookings', 'is_active']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-control form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'max_bookings': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TestBookingForm(forms.ModelForm):
    class Meta:
        model = TestBooking
        fields = ['date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': str(date.today())
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any notes for the lab (optional)'
            }),
        }

    def clean_date(self):
        booking_date = self.cleaned_data.get('date')
        if booking_date < date.today():
            raise forms.ValidationError('Please select a future date.')
        return booking_date


class TestResultForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Lab technician notes (optional)'
            }),
        }


class TestResultItemForm(forms.Form):
    """Dynamic form for filling test result values."""
    value = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave blank if not done'
        })
    )