from django.db import models


class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ('GENERAL', 'General Ward'),
        ('SEMI_PRIVATE', 'Semi Private'),
        ('PRIVATE', 'Private'),
        ('ICU', 'ICU'),
        ('EMERGENCY', 'Emergency'),
    ]

    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='GENERAL')
    floor = models.CharField(max_length=20, blank=True)
    capacity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room_number} ({self.get_room_type_display()})"

    @property
    def occupied_beds(self):
        return self.beds.filter(status='OCCUPIED').count()

    @property
    def available_beds(self):
        return self.beds.filter(status='AVAILABLE').count()


class RoomBed(models.Model):
    BED_STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('MAINTENANCE', 'Maintenance'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=20)
    status = models.CharField(max_length=15, choices=BED_STATUS_CHOICES, default='AVAILABLE')

    class Meta:
        unique_together = ['room', 'bed_number']
        ordering = ['room__room_number', 'bed_number']

    def __str__(self):
        return f"{self.room.room_number} - Bed {self.bed_number}"


class RoomAssignment(models.Model):
    STATUS_CHOICES = [
        ('ADMITTED', 'Admitted'),
        ('DISCHARGED', 'Discharged'),
        ('TRANSFERRED', 'Transferred'),
    ]

    patient = models.ForeignKey('users.PatientProfile', on_delete=models.CASCADE, related_name='room_assignments')
    bed = models.ForeignKey(RoomBed, on_delete=models.PROTECT, related_name='assignments')
    admitted_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='admitted_patients')
    doctor = models.ForeignKey('clinical.Doctor', on_delete=models.SET_NULL, null=True, blank=True, related_name='room_patients')
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ADMITTED')
    admitted_at = models.DateTimeField(auto_now_add=True)
    discharged_at = models.DateTimeField(null=True, blank=True)
    discharge_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-admitted_at']

    def __str__(self):
        return f"{self.patient.full_name} - {self.bed} - {self.status}"
