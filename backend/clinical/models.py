from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class e.g. bi-heart-pulse")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, related_name='doctors')
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bio = models.TextField(blank=True)
    experience_years = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='doctors/profile/', null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.user.username} - {self.specialization}"
    def get_average_rating(self):
        try:
            from django.db.models import Avg
            avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
            return round(avg, 1) if avg else 0
        except Exception:
            return 0

    def get_total_reviews(self):
        try:
            return self.reviews.count()
        except Exception:
            return 0

    class Meta:
        ordering = ['user__username']


class Shift(models.Model):
    SHIFT_CHOICES = [
        ('Morning', 'Morning'),
        ('Evening', 'Evening'),
        ('Night', 'Night'),
    ]
    name = models.CharField(max_length=20, choices=SHIFT_CHOICES, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField(default=30, help_text="Slot duration in minutes")

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class DoctorSchedule(models.Model):
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.doctor.user.username} - {self.day} - {self.shift.name}"

    class Meta:
        # Prevent duplicate schedule for same doctor on same day
        unique_together = ['doctor', 'day']
        ordering = ['day']


class DoctorLeave(models.Model):
    APPROVAL_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='leaves')
    date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_doctor_leaves',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.doctor.user.username} - Leave on {self.date}"

    class Meta:
        unique_together = ['doctor', 'date']
        ordering = ['-date']


class PatientVisit(models.Model):
    RISK_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='visits'
    )
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visit_report'
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_visits'
    )
    symptoms = models.TextField()
    vitals = models.JSONField(default=dict, blank=True)
    diagnosis = models.TextField(blank=True)
    doctor_notes = models.TextField(blank=True)
    prescribed_medicines = models.TextField(blank=True)
    suggested_tests = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)
    ai_possible_causes = models.TextField(blank=True)
    ai_recommended_tests = models.TextField(blank=True)
    ai_risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, default='LOW')
    ai_red_flags = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_patient_visits'
    )
    visit_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date']
        indexes = [
            models.Index(fields=['patient', '-visit_date']),
            models.Index(fields=['follow_up_date']),
            models.Index(fields=['ai_risk_level']),
        ]

    def __str__(self):
        return f"{self.patient.full_name} visit on {self.visit_date:%Y-%m-%d}"


class PatientDocument(models.Model):
    TYPE_CHOICES = [
        ('LAB_REPORT', 'Lab Report'),
        ('PRESCRIPTION', 'Prescription'),
        ('DISCHARGE', 'Discharge Summary'),
        ('SCAN', 'Scan/X-Ray'),
        ('OTHER', 'Other'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    visit = models.ForeignKey(
        PatientVisit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    title = models.CharField(max_length=180)
    document_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='OTHER')
    file = models.FileField(upload_to='patient_documents/')
    notes = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_patient_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [models.Index(fields=['patient', '-uploaded_at'])]

    def __str__(self):
        return f"{self.patient.full_name} - {self.title}"
