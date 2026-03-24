from django.contrib import admin
from .models import Appointment, WaitingList
from .no_show_predictor import NoShowPredictor, NoShowPredictor_Summary


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'date', 'start_time', 'status', 'created_at']
    list_filter = ['status', 'date']
    search_fields = ['patient__full_name', 'doctor__user__username']
    ordering = ['-date', '-start_time']


@admin.register(WaitingList)
class WaitingListAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date', 'priority', 'status', 'created_at']
    list_filter = ['date', 'status']


@admin.register(NoShowPredictor)
class NoShowPredictorAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'risk_level', 'no_show_probability', 'predicted_at', 'actually_no_showed']
    list_filter = ['risk_level', 'model_used', 'predicted_at']
    search_fields = ['appointment__patient__full_name', 'appointment__doctor__user__username']


@admin.register(NoShowPredictor_Summary)
class NoShowPredictorSummaryAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_appointments', 'high_risk_count', 'actual_no_shows', 'accuracy']
    ordering = ['-date']