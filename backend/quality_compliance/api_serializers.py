from rest_framework import serializers

from quality_compliance.models import BackupRestoreDrill
from quality_compliance.models import IncidentReport
from quality_compliance.models import RetentionPolicy
from quality_compliance.models import SlaBreach


def _full_name(user):
    if not user:
        return ''
    name = f'{getattr(user, "first_name", "")} {getattr(user, "last_name", "")}'.strip()
    return name or getattr(user, 'email', '') or ''


class IncidentReportSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = IncidentReport
        fields = [
            'id', 'title', 'incident_type', 'severity', 'status', 'description',
            'root_cause', 'corrective_action', 'preventive_action', 'closure_notes',
            'reported_by', 'reported_by_name', 'assigned_to', 'assigned_to_name',
            'reported_at', 'triaged_at', 'resolved_at', 'due_date',
        ]
        read_only_fields = ('reported_at', 'triaged_at', 'resolved_at', 'reported_by_name', 'assigned_to_name')

    def get_reported_by_name(self, obj):
        return _full_name(obj.reported_by)

    def get_assigned_to_name(self, obj):
        return _full_name(obj.assigned_to)


class SlaBreachSerializer(serializers.ModelSerializer):
    escalated_to_name = serializers.SerializerMethodField()
    acknowledged_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SlaBreach
        fields = [
            'id', 'process_name', 'reference_number', 'category', 'severity', 'status',
            'expected_at', 'breached_at', 'owner_role', 'description', 'resolution_summary',
            'escalated_to', 'escalated_to_name', 'acknowledged_by', 'acknowledged_by_name',
            'escalated_at', 'resolved_at',
        ]
        read_only_fields = ('breached_at', 'escalated_at', 'resolved_at', 'escalated_to_name', 'acknowledged_by_name')

    def get_escalated_to_name(self, obj):
        return _full_name(obj.escalated_to)

    def get_acknowledged_by_name(self, obj):
        return _full_name(obj.acknowledged_by)


class BackupRestoreDrillSerializer(serializers.ModelSerializer):
    executor_name = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()

    class Meta:
        model = BackupRestoreDrill
        fields = [
            'id', 'drill_type', 'environment', 'runbook_version', 'success', 'duration_minutes',
            'rpo_minutes', 'rto_minutes', 'notes', 'evidence_url', 'executor', 'executor_name',
            'verified_by', 'verified_by_name', 'verified_at', 'executed_at',
        ]
        read_only_fields = ('verified_at', 'executed_at', 'executor_name', 'verified_by_name')

    def get_executor_name(self, obj):
        return _full_name(obj.executor)

    def get_verified_by_name(self, obj):
        return _full_name(obj.verified_by)


class RetentionPolicySerializer(serializers.ModelSerializer):
    updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RetentionPolicy
        fields = [
            'id', 'module_name', 'policy_name', 'retention_days', 'archive_after_days', 'active',
            'owner_role', 'summary', 'last_executed_at', 'next_review_at', 'updated_by', 'updated_by_name',
            'updated_at',
        ]
        read_only_fields = ('last_executed_at', 'updated_at', 'updated_by_name')

    def get_updated_by_name(self, obj):
        return _full_name(obj.updated_by)