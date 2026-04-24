from django.contrib import admin

from .models import OTSchedule, ProcedureNote, PostOpNote


@admin.register(OTSchedule)
class OTScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'procedure_name', 'ot_room', 'scheduled_start', 'status')
    list_filter = ('status', 'ot_room')
    search_fields = ('patient__full_name', 'procedure_name')


@admin.register(ProcedureNote)
class ProcedureNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule', 'signed_by', 'signed_at')


@admin.register(PostOpNote)
class PostOpNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule', 'recovery_status', 'pain_score', 'created_at')
    list_filter = ('recovery_status',)
