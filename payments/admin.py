from django.contrib import admin
from .models import Payment, Refund, PaymentReminder, PaymentReminderLog, InsuranceVerification


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'amount', 'status', 'payment_method', 'paid_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['patient__full_name', 'doctor__user__username']
    ordering = ['-created_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment', 'status', 'refunded_at']
    list_filter = ['status']
    ordering = ['-created_at']


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