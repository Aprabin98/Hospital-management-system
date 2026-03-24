"""
No-Show Prediction Model and ML heuristics for appointments
Predicts which patients are likely to miss their appointments
"""

from django.db import models
from django.utils import timezone
from appointments.models import Appointment
from clinical.models import Doctor
from users.models import PatientProfile
from datetime import timedelta


class NoShowPredictor(models.Model):
    """Predicts appointment no-show probability"""
    
    PREDICTION_MODEL_CHOICES = [
        ('HEURISTIC', 'Rule-based Heuristic'),
        ('ML', 'Machine Learning'),
    ]

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='no_show_prediction'
    )
    
    # Prediction details
    model_used = models.CharField(
        max_length=10,
        choices=PREDICTION_MODEL_CHOICES,
        default='HEURISTIC'
    )
    
    no_show_probability = models.FloatField(
        default=0.0,
        help_text="Probability of no-show (0-1)"
    )
    
    risk_level = models.CharField(
        max_length=10,
        choices=[
            ('LOW', 'Low Risk (0-33%)'),
            ('MEDIUM', 'Medium Risk (33-66%)'),
            ('HIGH', 'High Risk (66-100%)'),
        ],
        default='LOW'
    )
    
    # Factor scores (0-100)
    patient_history_score = models.IntegerField(default=0)
    distance_score = models.IntegerField(default=0)
    reminder_score = models.IntegerField(default=0)
    time_score = models.IntegerField(default=0)
    doctor_score = models.IntegerField(default=0)
    weather_score = models.IntegerField(default=0)
    
    # Interventions
    reminder_sent = models.BooleanField(default=False)
    overbooking_compensation = models.BooleanField(
        default=False,
        help_text="If high no-show risk, overbookmultiple patients"
    )
    
    predicted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Outcome
    actually_no_showed = models.BooleanField(null=True, blank=True)
    prediction_accuracy = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Prediction for Appointment #{self.appointment.id} - {self.risk_level}"
    
    def predict_heuristic(self):
        """Rule-based heuristic prediction"""
        appointment = self.appointment
        patient = appointment.patient
        
        # Patient history factors (past no-shows)
        no_show_count = (
            Appointment.objects.filter(
                patient=patient,
                status='NO_SHOW',
                date__lt=appointment.date
            ).count()
        )
        self.patient_history_score = min(100, no_show_count * 15)  # 15% per past no-show
        
        # Distance to hospital (approximation from address)
        # Higher distance = higher no-show probability
        self.distance_score = 10  # Placeholder - could use geocoding API
        
        # Time of appointment
        # Late evening appointments have higher no-show rates
        if appointment.start_time.hour >= 18:
            self.time_score = 35
        elif appointment.start_time.hour >= 17:
            self.time_score = 20
        elif appointment.start_time.hour < 8:
            self.time_score = 15
        else:
            self.time_score = 5
        
        # Doctor popularity (from rating)
        doctor = appointment.doctor
        avg_rating = doctor.average_rating if hasattr(doctor, 'average_rating') else 4.0
        self.doctor_score = max(0, 50 - int(avg_rating * 10))  # Popular = fewer no-shows
        
        # Days until appointment
        days_until = (appointment.date - timezone.now().date()).days
        if days_until <= 1:
            self.reminder_score = 25  # Last minute bookings are risky
        elif days_until <= 7:
            self.reminder_score = 15
        else:
            self.reminder_score = 5
        
        # Calculate total probability
        factors = [
            self.patient_history_score * 0.30,  # 30% weight
            (self.distance_score + self.time_score) * 0.30,  # 30% weight
            self.doctor_score * 0.20,  # 20% weight
            self.reminder_score * 0.20,  # 20% weight
        ]
        
        self.no_show_probability = sum(factors) / 100.0
        
        # Determine risk level
        if self.no_show_probability < 0.33:
            self.risk_level = 'LOW'
        elif self.no_show_probability < 0.66:
            self.risk_level = 'MEDIUM'
        else:
            self.risk_level = 'HIGH'
        
        self.model_used = 'HEURISTIC'
        return self.no_show_probability


class NoShowPredictor_Summary(models.Model):
    """Daily aggregate stats on no-show predictions"""
    
    date = models.DateField(unique=True)
    
    total_appointments = models.IntegerField(default=0)
    high_risk_count = models.IntegerField(default=0)
    medium_risk_count = models.IntegerField(default=0)
    low_risk_count = models.IntegerField(default=0)
    
    actual_no_shows = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"No-Show Predictions for {self.date}"


# ===============================================
# NO-SHOW PREDICTION UTILITY FUNCTIONS
# ===============================================

class PredictionEngine:
    """Utility class for no-show predictions"""
    
    @staticmethod
    def predict_appointment(appointment):
        """Generate no-show prediction for appointment"""
        predictor, created = NoShowPredictor.objects.get_or_create(
            appointment=appointment,
            defaults={'risk_level': 'LOW'}
        )
        
        if created or (timezone.now() - predictor.predicted_at).days > 0:
            predictor.predict_heuristic()
            predictor.save()
        
        return predictor
    
    @staticmethod
    def get_high_risk_appointments():
        """Get all high-risk appointments for follow-up"""
        return (
            NoShowPredictor.objects.filter(
                risk_level='HIGH',
                reminder_sent=False,
                appointment__date__gte=timezone.now().date()
            )
            .select_related('appointment__patient__user', 'appointment__doctor__user')
        )
    
    @staticmethod
    def get_upcoming_appointments_predictions():
        """Get predictions for appointments in next 7 days"""
        upcoming = Appointment.objects.filter(
            date__range=[
                timezone.now().date(),
                timezone.now().date() + timedelta(days=7)
            ],
            status__in=['PENDING', 'CONFIRMED']
        )
        
        predictions = []
        for apt in upcoming:
            pred = PredictionEngine.predict_appointment(apt)
            predictions.append(pred)
        
        return predictions
    
    @staticmethod
    def calculate_accuracy():
        """Calculate overall accuracy of predictions"""
        predictions = NoShowPredictor.objects.filter(
            actually_no_showed__isnull=False
        )
        
        if not predictions.exists():
            return 0.0
        
        correct = 0
        for pred in predictions:
            # High risk and no-showed = correct
            if pred.risk_level == 'HIGH' and pred.actually_no_showed:
                correct += 1
            # Low/medium risk and showed = correct
            elif pred.risk_level in ['LOW', 'MEDIUM'] and not pred.actually_no_showed:
                correct += 1
        
        return (correct / len(predictions)) * 100
