from django.contrib import admin
from .models import Appointment, WaitingList


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'date', 'start_time', 'status', 'created_at']
    list_filter = ['status', 'date']
    search_fields = ['patient__full_name', 'doctor__user__username']
    ordering = ['-date', '-start_time']


@admin.register(WaitingList)
class WaitingListAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date', 'created_at']
    list_filter = ['date']