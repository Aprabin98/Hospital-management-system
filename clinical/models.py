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
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='leaves')
    date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.doctor.user.username} - Leave on {self.date}"

    class Meta:
        unique_together = ['doctor', 'date']
        ordering = ['-date']