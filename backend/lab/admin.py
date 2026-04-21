from django.contrib import admin
from .models import (
    TestTemplate, TestField, TestSchedule, TestBooking, TestResult, TestResultItem,
    LabSample, QCLog, CriticalValueAcknowledgment
)


class TestFieldInline(admin.TabularInline):
    model = TestField
    extra = 1


class TestScheduleInline(admin.TabularInline):
    model = TestSchedule
    extra = 1


@admin.register(TestTemplate)
class TestTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_minutes', 'is_available']
    inlines = [TestFieldInline, TestScheduleInline]


@admin.register(TestBooking)
class TestBookingAdmin(admin.ModelAdmin):
    list_display = ['patient', 'template', 'date', 'status', 'payment_status', 'amount']
    list_filter = ['status', 'payment_status']
    search_fields = ['patient__full_name', 'template__name']


class TestResultItemInline(admin.TabularInline):
    model = TestResultItem
    extra = 0


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['booking', 'filled_by', 'is_released', 'filled_at']
    list_filter = ['is_released']
    inlines = [TestResultItemInline]


# ==================== PHASE 4 Admin Registrations ====================

@admin.register(LabSample)
class LabSampleAdmin(admin.ModelAdmin):
    list_display = ['barcode_id', 'result', 'status', 'collected_by', 'collected_at', 'validated_by']
    list_filter = ['status', 'collected_at', 'validated_at']
    search_fields = ['barcode_id', 'result__booking__patient__full_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Sample Information', {
            'fields': ('result', 'barcode_id', 'status')
        }),
        ('Collection', {
            'fields': ('collected_by', 'collected_at')
        }),
        ('Processing', {
            'fields': ('processed_by', 'processed_at')
        }),
        ('Validation', {
            'fields': ('validated_by', 'validated_at')
        }),
        ('Rejection/Recollection', {
            'fields': ('rejection_reason', 'recollect_reason')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QCLog)
class QCLogAdmin(admin.ModelAdmin):
    list_display = ['qc_type', 'test_template', 'result', 'performed_by', 'performed_at']
    list_filter = ['qc_type', 'result', 'performed_at']
    search_fields = ['test_template__name', 'details', 'performed_by__email']
    readonly_fields = ['performed_at']
    fieldsets = (
        ('QC Information', {
            'fields': ('qc_type', 'test_template', 'sample')
        }),
        ('Details', {
            'fields': ('details', 'reference_value', 'actual_value', 'deviation')
        }),
        ('Result', {
            'fields': ('result', 'performed_by', 'performed_at')
        }),
    )


@admin.register(CriticalValueAcknowledgment)
class CriticalValueAcknowledgmentAdmin(admin.ModelAdmin):
    list_display = ['result', 'urgency', 'is_critical', 'notification_sent_at', 'acknowledged_by', 'acknowledged_at']
    list_filter = ['urgency', 'is_critical', 'acknowledged_at', 'notification_method']
    search_fields = ['result__booking__patient__full_name', 'acknowledgment_notes']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Critical Value Information', {
            'fields': ('result', 'is_critical', 'urgency', 'critical_fields')
        }),
        ('Notification', {
            'fields': ('notification_method', 'notification_sent_at')
        }),
        ('Doctor Acknowledgment', {
            'fields': ('acknowledged_by', 'acknowledged_at', 'acknowledgment_notes')
        }),
        ('Escalation', {
            'fields': ('escalated_to', 'escalated_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
