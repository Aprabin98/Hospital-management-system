from django import forms
from django.contrib.auth import get_user_model
from .models import PatientProfile, PatientHealthRecord, PatientVitalLog

User = get_user_model()


class PatientRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'password']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'PATIENT'
        user.is_active = False  # Needs email activation
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )


class TwoFactorVerifyForm(forms.Form):
    code = forms.CharField(
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={'placeholder': '6-digit code'}),
    )

    def clean_code(self):
        code = (self.cleaned_data.get('code') or '').strip()
        if not code.isdigit():
            raise forms.ValidationError('Enter a valid 6-digit numeric code.')
        return code


class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = [
            'full_name', 'phone', 'gender', 'date_of_birth',
            'blood_group', 'height', 'weight', 'image',
            'address', 'emergency_contact'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'height': forms.NumberInput(attrs={'placeholder': 'Height in cm'}),
            'weight': forms.NumberInput(attrs={'placeholder': 'Weight in kg'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Address'}),
            'emergency_contact': forms.TextInput(attrs={'placeholder': 'Emergency Contact Number'}),
        }


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your registered email'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('No account found with this email.')
        return email


class SetNewPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data


class PatientHealthRecordForm(forms.ModelForm):
    class Meta:
        model = PatientHealthRecord
        fields = [
            'allergies',
            'chronic_conditions',
            'surgical_history',
            'family_history',
            'current_medications',
            'immunization_notes',
            'emergency_notes',
        ]
        widgets = {
            'allergies': forms.Textarea(attrs={'rows': 2}),
            'chronic_conditions': forms.Textarea(attrs={'rows': 2}),
            'surgical_history': forms.Textarea(attrs={'rows': 2}),
            'family_history': forms.Textarea(attrs={'rows': 2}),
            'current_medications': forms.Textarea(attrs={'rows': 2}),
            'immunization_notes': forms.Textarea(attrs={'rows': 2}),
            'emergency_notes': forms.Textarea(attrs={'rows': 2}),
        }


class PatientVitalLogForm(forms.ModelForm):
    class Meta:
        model = PatientVitalLog
        fields = [
            'blood_pressure',
            'pulse',
            'temperature_c',
            'respiratory_rate',
            'oxygen_saturation',
            'weight_kg',
            'height_cm',
            'notes',
        ]