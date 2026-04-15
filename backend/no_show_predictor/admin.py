from django.contrib import admin

from .models import NoShowPredictionLog


@admin.register(NoShowPredictionLog)
class NoShowPredictionLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'patient',
        'doctor',
        'appointment_date',
        'risk_score',
        'risk_level',
        'created_at',
    )
    list_filter = ('risk_level', 'appointment_date', 'created_at')
    search_fields = (
        'patient__full_name',
        'patient__user__email',
        'doctor__user__username',
    )
    readonly_fields = ('created_at',)
