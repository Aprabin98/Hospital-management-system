from django.contrib import admin

from .models import DrugInteraction, InteractionCheckLog


@admin.register(DrugInteraction)
class DrugInteractionAdmin(admin.ModelAdmin):
    list_display = ('drug_a', 'drug_b', 'severity', 'is_active', 'source')
    list_filter = ('severity', 'is_active')
    search_fields = ('drug_a', 'drug_b', 'description', 'management')


@admin.register(InteractionCheckLog)
class InteractionCheckLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'checked_by', 'interactions_found', 'worst_severity', 'created_at')
    list_filter = ('worst_severity',)
    search_fields = ('checked_by__email',)
