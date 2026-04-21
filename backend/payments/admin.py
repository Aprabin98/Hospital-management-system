from django.contrib import admin
from .models import (
    Payment, Refund, PaymentReminder, PaymentReminderLog, InsuranceVerification,
    Invoice, InvoiceLineItem, InsuranceClaim, ClaimAuditLog, DenialRework, InsurancePreAuth
)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'amount', 'status', 'payment_method', 'paid_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['patient__full_name', 'doctor__user__username']
    ordering = ['-created_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment', 'status', 'amount', 'requested_by', 'refund_method', 'updated_at']
    list_filter = ['status', 'refund_method']
    search_fields = ['payment__patient__full_name']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = ['payment', 'reminder_type', 'channel', 'is_active', 'updated_at']
    list_filter = ['reminder_type', 'channel', 'is_active']
    search_fields = ['payment__patient__full_name', 'payment__id']


@admin.register(PaymentReminderLog)
class PaymentReminderLogAdmin(admin.ModelAdmin):
    list_display = ['payment', 'reminder_number', 'channel', 'status', 'sent_at']
    list_filter = ['status', 'channel', 'reminder_number']
    search_fields = ['payment__patient__full_name', 'recipient']
    ordering = ['-sent_at']


@admin.register(InsuranceVerification)
class InsuranceVerificationAdmin(admin.ModelAdmin):
    list_display = ['patient', 'provider_name', 'policy_number', 'coverage_percent', 'status', 'valid_until']
    list_filter = ['status', 'provider_name']
    search_fields = ['patient__full_name', 'policy_number', 'provider_name']
    ordering = ['-created_at']


# Phase 7: Finance & Insurance Maturity Models

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'patient', 'invoice_type', 'total_amount', 'amount_paid', 'status', 'due_date']
    list_filter = ['status', 'invoice_type', 'created_at']
    search_fields = ['invoice_number', 'patient__full_name']
    readonly_fields = ['created_at', 'created_by']
    ordering = ['-created_at']
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'invoice_type', 'patient', 'appointment')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'amount_paid')
        }),
        ('Insurance', {
            'fields': ('insurance_verification', 'insurance_amount', 'patient_amount')
        }),
        ('Status', {
            'fields': ('status', 'due_date')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at')
        })
    )


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 0
    fields = ['description', 'quantity', 'unit_price', 'total', 'appointment', 'lab_booking']
    readonly_fields = ['total']


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'total']
    list_filter = ['invoice__created_at']
    search_fields = ['invoice__invoice_number', 'description']
    ordering = ['-invoice__created_at']


class ClaimAuditLogInline(admin.TabularInline):
    model = ClaimAuditLog
    extra = 0
    fields = ['old_status', 'new_status', 'changed_by', 'change_reason', 'changed_at']
    readonly_fields = ['changed_at']


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = ['claim_number', 'patient', 'invoice', 'claimed_amount', 'approved_amount', 'status', 'days_pending']
    list_filter = ['status', 'submitted_at']
    search_fields = ['claim_number', 'patient__full_name', 'invoice__invoice_number']
    readonly_fields = ['submitted_at', 'received_at', 'approved_at', 'submitted_by', 'days_pending']
    ordering = ['-submitted_at']
    inlines = [ClaimAuditLogInline]
    fieldsets = (
        ('Claim Information', {
            'fields': ('claim_number', 'invoice', 'patient', 'insurance_verification')
        }),
        ('Amounts', {
            'fields': ('claimed_amount', 'approved_amount', 'reduction_reason')
        }),
        ('Status & Timeline', {
            'fields': ('status', 'submitted_at', 'received_at', 'approved_at', 'days_pending')
        }),
        ('Submission', {
            'fields': ('submitted_by', 'submission_reference', 'submission_notes')
        })
    )


@admin.register(ClaimAuditLog)
class ClaimAuditLogAdmin(admin.ModelAdmin):
    list_display = ['claim', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['new_status', 'changed_at']
    search_fields = ['claim__claim_number', 'change_reason']
    readonly_fields = ['changed_at']
    ordering = ['-changed_at']


@admin.register(DenialRework)
class DenialReworkAdmin(admin.ModelAdmin):
    list_display = ['claim', 'status', 'assigned_to', 'original_denial_reason', 'resubmit_date']
    list_filter = ['status', 'created_at', 'assigned_to']
    search_fields = ['claim__claim_number', 'original_denial_reason']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    fieldsets = (
        ('Denial Information', {
            'fields': ('claim', 'original_denial_reason', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'correction_notes', 'resubmit_date')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(InsurancePreAuth)
class InsurancePreAuthAdmin(admin.ModelAdmin):
    list_display = ['pre_auth_number', 'patient', 'insurance_verification', 'treatment_code', 'estimated_amount', 'approved_amount', 'status']
    list_filter = ['status', 'created_at']
    search_fields = ['pre_auth_number', 'patient__full_name', 'treatment_code']
    readonly_fields = ['pre_auth_number', 'created_at']
    ordering = ['-created_at']
    fieldsets = (
        ('Pre-Authorization Request', {
            'fields': ('pre_auth_number', 'patient', 'insurance_verification', 'treatment_code')
        }),
        ('Amounts', {
            'fields': ('estimated_amount', 'approved_amount')
        }),
        ('Status & Validity', {
            'fields': ('status', 'valid_from', 'valid_until')
        }),
        ('Audit', {
            'fields': ('created_at',)
        })
    )