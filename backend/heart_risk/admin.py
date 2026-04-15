from django.contrib import admin

from .models import HeartRiskAssessment


@admin.register(HeartRiskAssessment)
class HeartRiskAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'patient',
        'risk_score',
        'risk_level',
        'assessed_by',
        'created_at',
    )
    list_filter = ('risk_level', 'created_at')
    search_fields = ('patient__full_name', 'patient__user__email', 'assessed_by__email')
