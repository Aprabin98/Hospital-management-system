from django.contrib import admin

from quality_compliance.models import BackupRestoreDrill
from quality_compliance.models import IncidentReport
from quality_compliance.models import RetentionPolicy
from quality_compliance.models import SlaBreach


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'incident_type', 'severity', 'status', 'reported_at', 'assigned_to')
    list_filter = ('incident_type', 'severity', 'status', 'reported_at')
    search_fields = ('title', 'description', 'root_cause', 'corrective_action')
    readonly_fields = ('reported_at', 'triaged_at', 'resolved_at')
    fieldsets = (
        ('Incident', {'fields': ('title', 'incident_type', 'severity', 'status', 'description')}),
        ('Ownership', {'fields': ('reported_by', 'assigned_to', 'due_date')}),
        ('Analysis', {'fields': ('root_cause', 'corrective_action', 'preventive_action', 'closure_notes')}),
        ('Timeline', {'fields': ('reported_at', 'triaged_at', 'resolved_at')}),
    )


@admin.register(SlaBreach)
class SlaBreachAdmin(admin.ModelAdmin):
    list_display = ('process_name', 'category', 'severity', 'status', 'expected_at', 'breached_at')
    list_filter = ('category', 'severity', 'status', 'expected_at', 'breached_at')
    search_fields = ('process_name', 'reference_number', 'description', 'resolution_summary')
    readonly_fields = ('breached_at', 'escalated_at', 'resolved_at')


@admin.register(BackupRestoreDrill)
class BackupRestoreDrillAdmin(admin.ModelAdmin):
    list_display = ('drill_type', 'environment', 'success', 'duration_minutes', 'executed_at', 'verified_at')
    list_filter = ('drill_type', 'success', 'environment', 'executed_at')
    search_fields = ('environment', 'runbook_version', 'notes')
    readonly_fields = ('executed_at', 'verified_at')


@admin.register(RetentionPolicy)
class RetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ('module_name', 'policy_name', 'retention_days', 'archive_after_days', 'active', 'next_review_at')
    list_filter = ('active', 'module_name', 'next_review_at')
    search_fields = ('module_name', 'policy_name', 'summary')
    readonly_fields = ('updated_at', 'last_executed_at')