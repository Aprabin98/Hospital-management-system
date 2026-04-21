from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('RECEPTIONIST', 'Receptionist'),
        ('LAB_TECHNICIAN', 'Lab Technician'),
        ('PHARMACIST', 'Pharmacist'),
        ('BILLING_OFFICER', 'Billing Officer'),
        ('INSURANCE_COORDINATOR', 'Insurance Coordinator'),
        ('QUALITY_COMPLIANCE_OFFICER', 'Quality Compliance Officer'),
        ('ADMIN', 'Super Admin'),
    ]

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50)
    first_name = models.CharField(max_length=150, blank=True, default='')
    last_name = models.CharField(max_length=150, blank=True, default='')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='PATIENT')
    is_active = models.BooleanField(default=False)  # False until email activated
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Email activation token
    activation_token = models.CharField(max_length=200, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.role})"

    def is_patient(self):
        return self.role == 'PATIENT'

    def is_doctor(self):
        return self.role == 'DOCTOR'

    def is_admin(self):
        return self.role == 'ADMIN'

    def is_quality_compliance_officer(self):
        return self.role == 'QUALITY_COMPLIANCE_OFFICER'
    
    def is_receptionist(self):
        return self.role == 'RECEPTIONIST'

    def is_nurse(self):
        return self.role == 'NURSE'
    
    def is_pharmacist(self):
        return self.role == 'PHARMACIST'
    
    def is_lab_technician(self):
        return self.role == 'LAB_TECHNICIAN'


class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    image = models.ImageField(upload_to='patients/profile/', null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.user.email}"

    def get_age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class PatientHealthRecord(models.Model):
    patient = models.OneToOneField(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='health_record'
    )
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    surgical_history = models.TextField(blank=True)
    family_history = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    immunization_notes = models.TextField(blank=True)
    emergency_notes = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_health_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Health record for {self.patient.full_name}"


class PatientVitalLog(models.Model):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='vital_logs'
    )
    blood_pressure = models.CharField(max_length=20, blank=True)
    pulse = models.PositiveIntegerField(null=True, blank=True)
    temperature_c = models.FloatField(null=True, blank=True)
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_vitals'
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Vitals for {self.patient.full_name} at {self.recorded_at}"


class PatientAllergy(models.Model):
    SEVERITY_CHOICES = [
        ('MILD', 'Mild'),
        ('MODERATE', 'Moderate'),
        ('SEVERE', 'Severe'),
        ('LIFE_THREATENING', 'Life Threatening'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('RESOLVED', 'Resolved'),
        ('UNKNOWN', 'Unknown'),
    ]

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='allergies'
    )
    allergen = models.CharField(max_length=150)
    reaction = models.CharField(max_length=255, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MODERATE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    diagnosed_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_allergies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['allergen']),
        ]

    def __str__(self):
        return f"{self.patient.full_name} - {self.allergen} ({self.severity})"


class LoginAttempt(models.Model):
    identifier = models.CharField(max_length=255, unique=True)
    failed_count = models.PositiveIntegerField(default=0)
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    last_attempt = models.DateTimeField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-last_attempt']

    def __str__(self):
        return f"{self.identifier} ({self.failed_count})"


class TwoFactorCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='two_factor_codes')
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['expires_at']),
        ]

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"2FA for {self.user.email} ({'used' if self.is_used else 'pending'})"