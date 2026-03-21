from django.contrib import admin
from .models import Payment, Refund


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