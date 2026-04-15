from django import forms
from .models import Payment, Refund, InsuranceVerification


class MarkPaidForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method', 'notes']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any notes (optional)'
            }),
        }


class RefundRequestForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Reason for refund request...'
            }),
        }


class RefundActionForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Admin notes...'
            }),
        }


class InsuranceVerificationForm(forms.ModelForm):
    class Meta:
        model = InsuranceVerification
        fields = [
            'provider_name',
            'policy_number',
            'plan_name',
            'coverage_percent',
            'valid_until',
        ]
        widgets = {
            'provider_name': forms.TextInput(attrs={'class': 'form-control'}),
            'policy_number': forms.TextInput(attrs={'class': 'form-control'}),
            'plan_name': forms.TextInput(attrs={'class': 'form-control'}),
            'coverage_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class InsuranceVerificationActionForm(forms.ModelForm):
    class Meta:
        model = InsuranceVerification
        fields = ['status', 'verification_notes', 'external_reference']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control form-select'}),
            'verification_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'external_reference': forms.TextInput(attrs={'class': 'form-control'}),
        }