from django.contrib import admin
from .models import TestTemplate, TestField, TestSchedule, TestBooking, TestResult, TestResultItem


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