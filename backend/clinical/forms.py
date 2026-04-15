from django import forms
from django.contrib.auth import get_user_model
from .models import Specialization, Doctor, Shift, DoctorSchedule, DoctorLeave

User = get_user_model()


class DoctorCreationForm(forms.Form):
    """Admin creates doctor account."""
    # User fields
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Doctor Email'})
    )
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'})
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Temporary Password'})
    )

    # Doctor fields
    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    consultation_fee = forms.DecimalField(
        max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Consultation Fee'})
    )
    experience_years = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Years of Experience'})
    )
    phone = forms.CharField(
        max_length=15, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Doctor Bio'})
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def save(self):
        # Create User
        user = User.objects.create_user(
            email=self.cleaned_data['email'],
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            role='DOCTOR',
            is_active=True  # Admin created accounts are active immediately
        )
        # Create Doctor profile
        doctor = Doctor.objects.create(
            user=user,
            specialization=self.cleaned_data['specialization'],
            consultation_fee=self.cleaned_data['consultation_fee'],
            experience_years=self.cleaned_data['experience_years'],
            phone=self.cleaned_data.get('phone', ''),
            bio=self.cleaned_data.get('bio', ''),
        )
        if self.cleaned_data.get('photo'):
            doctor.photo = self.cleaned_data['photo']
            doctor.save()
        return doctor


class DoctorEditForm(forms.ModelForm):
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Doctor
        fields = ['specialization', 'consultation_fee', 'experience_years', 'phone', 'bio', 'photo', 'is_available']
        widgets = {
            'specialization': forms.Select(attrs={'class': 'form-control'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username

    def save(self, commit=True):
        doctor = super().save(commit=False)
        doctor.user.username = self.cleaned_data['username']
        doctor.user.save()
        if commit:
            doctor.save()
        return doctor


class SpecializationForm(forms.ModelForm):
    class Meta:
        model = Specialization
        fields = ['name', 'description', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specialization Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. bi-heart-pulse'}),
        }


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['name', 'start_time', 'end_time', 'slot_duration']
        widgets = {
            'name': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'slot_duration': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class DoctorScheduleForm(forms.ModelForm):
    class Meta:
        model = DoctorSchedule
        fields = ['doctor', 'day', 'shift', 'is_active']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'day': forms.Select(attrs={'class': 'form-control'}),
            'shift': forms.Select(attrs={'class': 'form-control'}),
        }


class DoctorLeaveForm(forms.ModelForm):
    class Meta:
        model = DoctorLeave
        fields = ['date', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reason for leave'}),
        }


class DoctorSearchForm(forms.Form):
    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.filter(is_active=True),
        required=False,
        empty_label="All Specializations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by doctor name...'})
    )