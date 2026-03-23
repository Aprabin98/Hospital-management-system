from django import forms

from .models import DrugInteraction


class DrugInteractionForm(forms.ModelForm):
    class Meta:
        model = DrugInteraction
        fields = [
            'drug_a',
            'drug_b',
            'severity',
            'description',
            'management',
            'source',
            'is_active',
        ]
        widgets = {
            'drug_a': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Warfarin'}),
            'drug_b': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Aspirin'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'management': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dr sara joshi'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
