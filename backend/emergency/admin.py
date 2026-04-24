from django.contrib import admin

from .models import EmergencyClinicalNote, EmergencyEncounter, EmergencyTriage


@admin.register(EmergencyEncounter)
class EmergencyEncounterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'patient',
        'status',
        'triage_level',
        'severity_priority',
        'arrival_mode',
        'arrived_at',
    )
    list_filter = ('status', 'triage_level', 'arrival_mode')
    search_fields = ('patient__full_name', 'patient__user__email', 'chief_complaint')


@admin.register(EmergencyTriage)
class EmergencyTriageAdmin(admin.ModelAdmin):
    list_display = ('id', 'encounter', 'pain_score', 'oxygen_saturation', 'created_at')
    search_fields = ('encounter__patient__full_name',)


@admin.register(EmergencyClinicalNote)
class EmergencyClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'encounter', 'note_type', 'authored_by', 'created_at')
    list_filter = ('note_type',)
    search_fields = ('encounter__patient__full_name', 'content')
