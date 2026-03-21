from django.db import models

class Payment(models.Model):
    STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
    ]

    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('KHALTI', 'Khalti'),
        ('ESEWA', 'eSewa'),
        ('ONLINE', 'Online'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('APPOINTMENT', 'Appointment'),
        ('LAB_TEST', 'Lab Test'),
    ]

    payment_type = models.CharField(
        max_length=15,
        choices=PAYMENT_TYPE_CHOICES,
        default='APPOINTMENT'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='payments',
        null=True, blank=True
    )
    lab_booking = models.ForeignKey(
        'lab.TestBooking',
        on_delete=models.CASCADE,
        related_name='payments',
        null=True, blank=True
    )

    patient = models.ForeignKey(
        'users.PatientProfile',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    doctor = models.ForeignKey(
    'clinical.Doctor',
    on_delete=models.CASCADE,
    related_name='payments',
    null=True, blank=True
    )
    
    # Store amount at time of booking (fee might change later)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='UNPAID'
    )
    payment_method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES,
        default='CASH',
        blank=True
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    receipt_file = models.FileField(
        upload_to='payments/receipts/',
        null=True, blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.patient.full_name} - Rs.{self.amount} - {self.status}"


class Refund(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='refund'
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    refunded_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund for Payment #{self.payment.id} - {self.status}"