from django.db import models
from django.utils import timezone


class InpatientStay(models.Model):
    STATUS_CHOICES = [
        ('ADMITTED', 'Admitted'),
        ('DISCHARGED', 'Discharged'),
        ('TRANSFERRED', 'Transferred'),
    ]

    patient = models.ForeignKey('users.PatientProfile', on_delete=models.CASCADE, related_name='inpatient_stays')
    attending_doctor = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inpatient_stays',
    )
    admission_request = models.ForeignKey(
        'rooms.AdmissionRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inpatient_stays',
    )
    room_assignment = models.ForeignKey(
        'rooms.RoomAssignment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inpatient_stays',
    )
    admission_appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inpatient_stays',
    )

    primary_diagnosis = models.CharField(max_length=255)
    admission_reason = models.TextField(blank=True)
    care_notes = models.TextField(blank=True)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ADMITTED')
    expected_discharge_date = models.DateField(null=True, blank=True)
    actual_discharge_date = models.DateField(null=True, blank=True)

    admitted_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='ipd_admitted_by')
    admission_datetime = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-admission_datetime']
        indexes = [
            models.Index(fields=['status', '-admission_datetime']),
            models.Index(fields=['patient', '-admission_datetime']),
        ]

    def __str__(self):
        return f"IPD #{self.id} - {self.patient.full_name} ({self.status})"

    @property
    def length_of_stay_days(self):
        start_date = self.admission_datetime.date()
        end_date = self.actual_discharge_date or timezone.localdate()
        return max((end_date - start_date).days, 0)


class ProgressNote(models.Model):
    NOTE_TYPE_CHOICES = [
        ('PROGRESS', 'Progress Note'),
        ('ROUND', 'Round Note'),
        ('NURSING', 'Nursing Note'),
    ]

    inpatient_stay = models.ForeignKey(InpatientStay, on_delete=models.CASCADE, related_name='progress_notes')
    author = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='ipd_progress_notes')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='PROGRESS')
    clinical_findings = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.note_type} - Stay #{self.inpatient_stay_id}"


class DailyRound(models.Model):
    inpatient_stay = models.ForeignKey(InpatientStay, on_delete=models.CASCADE, related_name='daily_rounds')
    round_date = models.DateField(default=timezone.localdate)
    round_assessor = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='ipd_rounds_assessed')
    round_notes = models.TextField()
    vital_assessment = models.TextField(blank=True)
    current_status = models.CharField(max_length=120, blank=True)
    orders = models.TextField(blank=True)
    is_signed = models.BooleanField(default=False)
    signed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ipd_rounds_signed',
    )
    signed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-round_date', '-created_at']
        indexes = [
            models.Index(fields=['round_date']),
            models.Index(fields=['inpatient_stay', '-round_date']),
        ]

    def __str__(self):
        return f"Round #{self.id} - Stay #{self.inpatient_stay_id}"


class MedicationAdministrationRecord(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('GIVEN', 'Given'),
        ('OMITTED', 'Omitted'),
        ('DELAYED', 'Delayed'),
    ]

    inpatient_stay = models.ForeignKey(InpatientStay, on_delete=models.CASCADE, related_name='mar_entries')
    prescription_item = models.ForeignKey(
        'prescriptions.PrescriptionItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mar_entries',
    )
    medication_name = models.CharField(max_length=255)
    dose_given = models.CharField(max_length=120)
    route = models.CharField(max_length=80, blank=True)

    scheduled_datetime = models.DateTimeField()
    administered_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='SCHEDULED')
    administered_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ipd_mar_administered',
    )
    reason_not_given = models.TextField(blank=True)
    deviations = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_datetime']
        indexes = [
            models.Index(fields=['status', 'scheduled_datetime']),
            models.Index(fields=['inpatient_stay', '-scheduled_datetime']),
        ]

    def __str__(self):
        return f"MAR #{self.id} - {self.medication_name}"


class ProcedureSchedule(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    inpatient_stay = models.ForeignKey(InpatientStay, on_delete=models.CASCADE, related_name='procedures')
    procedure_name = models.CharField(max_length=255)
    scheduled_datetime = models.DateTimeField()
    ot_room_number = models.CharField(max_length=50, blank=True)
    surgeon = models.ForeignKey(
        'clinical.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ipd_procedures',
    )
    indication = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='SCHEDULED')
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_datetime']

    def __str__(self):
        return f"{self.procedure_name} - Stay #{self.inpatient_stay_id}"


class DischargePackage(models.Model):
    inpatient_stay = models.OneToOneField(InpatientStay, on_delete=models.CASCADE, related_name='discharge_package')

    discharge_date = models.DateField(default=timezone.localdate)
    discharge_summary = models.TextField()
    discharge_diagnoses = models.TextField(blank=True)
    discharge_instructions = models.TextField()
    follow_up_date = models.DateField()
    follow_up_provider = models.CharField(max_length=255, blank=True)
    follow_up_specialty = models.CharField(max_length=255, blank=True)

    doctor_signed_off_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ipd_discharges_signed',
    )
    doctor_signed_off_at = models.DateTimeField(null=True, blank=True)
    patient_acknowledged_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ipd_discharges_acknowledged',
    )
    patient_acknowledged_at = models.DateTimeField(null=True, blank=True)

    nursing_clearance = models.BooleanField(default=False)
    pharmacy_clearance = models.BooleanField(default=False)
    billing_clearance = models.BooleanField(default=False)
    final_approved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Discharge - Stay #{self.inpatient_stay_id}"

    @property
    def checklist_complete(self):
        return all([
            bool(self.discharge_summary.strip()),
            bool(self.discharge_instructions.strip()),
            self.nursing_clearance,
            self.pharmacy_clearance,
            self.billing_clearance,
            self.doctor_signed_off_at is not None,
        ])
