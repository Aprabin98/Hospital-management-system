from django import forms
from .models import Payment, Refund


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