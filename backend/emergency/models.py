from django.db import models


class EmergencyEncounter(models.Model):
    ARRIVAL_MODE_CHOICES = [
        ('WALK_IN', 'Walk-in'),
        ('AMBULANCE', 'Ambulance'),
        ('REFERRAL', 'Referral'),
        ('POLICE', 'Police'),
        ('OTHER', 'Other'),
    ]

    TRIAGE_LEVEL_CHOICES = [
        ('ESI_1', 'ESI 1 - Immediate'),
        ('ESI_2', 'ESI 2 - Emergent'),
        ('ESI_3', 'ESI 3 - Urgent'),
        ('ESI_4', 'ESI 4 - Less Urgent'),
        ('ESI_5', 'ESI 5 - Non Urgent'),
    ]

    STATUS_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('TRIAGED', 'Triaged'),
        ('IN_TREATMENT', 'In Treatment'),
        ('ADMITTED', 'Admitted'),
        ('TRANSFERRED', 'Transferred'),
        ('DISCHARGED', 'Discharged'),
        ('DECEASED', 'Deceased'),
    ]

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='emergency_encounters',
    )
    assigned_doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_encounters',
    )
    arrival_mode = models.CharField(max_length=20, choices=ARRIVAL_MODE_CHOICES, default='WALK_IN')
    triage_level = models.CharField(max_length=10, choices=TRIAGE_LEVEL_CHOICES, blank=True)
    severity_priority = models.PositiveSmallIntegerField(default=5)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTERED')
    chief_complaint = models.TextField()
    stabilization_notes = models.TextField(blank=True)
    disposition_notes = models.TextField(blank=True)
    arrived_at = models.DateTimeField(auto_now_add=True)
    triaged_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_emergency_encounters',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-arrived_at']
        indexes = [
            models.Index(fields=['status', '-arrived_at']),
            models.Index(fields=['severity_priority', '-arrived_at']),
        ]

    def __str__(self):
        return f"ED-{self.id} {self.patient.full_name} ({self.status})"


class EmergencyTriage(models.Model):
    encounter = models.ForeignKey(
        EmergencyEncounter,
        on_delete=models.CASCADE,
        related_name='triage_records',
    )
    pulse = models.PositiveIntegerField(null=True, blank=True)
    systolic_bp = models.PositiveIntegerField(null=True, blank=True)
    diastolic_bp = models.PositiveIntegerField(null=True, blank=True)
    temperature_c = models.FloatField(null=True, blank=True)
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True)
    pain_score = models.PositiveSmallIntegerField(default=0)
    triage_notes = models.TextField(blank=True)
    triaged_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_triage_entries',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Triage {self.encounter_id} @ {self.created_at}"


class EmergencyClinicalNote(models.Model):
    NOTE_TYPE_CHOICES = [
        ('NURSING', 'Nursing'),
        ('DOCTOR', 'Doctor'),
        ('STABILIZATION', 'Stabilization'),
        ('GENERAL', 'General'),
    ]

    encounter = models.ForeignKey(
        EmergencyEncounter,
        on_delete=models.CASCADE,
        related_name='clinical_notes',
    )
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='GENERAL')
    content = models.TextField()
    authored_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergency_notes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.note_type} note for ED-{self.encounter_id}"
