from django.contrib import admin

from .models import AdmissionRequest, Room, RoomAssignment, RoomBed


class RoomBedInline(admin.TabularInline):
    model = RoomBed
    extra = 0


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'floor', 'capacity', 'is_active']
    list_filter = ['room_type', 'is_active', 'floor']
    search_fields = ['room_number', 'floor']
    inlines = [RoomBedInline]


@admin.register(RoomAssignment)
class RoomAssignmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'bed', 'doctor', 'status', 'admitted_at', 'discharged_at']
    list_filter = ['status', 'admitted_at']
    search_fields = ['patient__full_name', 'bed__room__room_number']


@admin.register(RoomBed)
class RoomBedAdmin(admin.ModelAdmin):
    list_display = ['room', 'bed_number', 'status']
    list_filter = ['status', 'room__room_type']
    search_fields = ['room__room_number', 'bed_number']


@admin.register(AdmissionRequest)
class AdmissionRequestAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'status', 'preferred_room_type', 'created_at', 'processed_at']
    list_filter = ['status', 'preferred_room_type', 'created_at']
    search_fields = ['patient__full_name', 'doctor__user__username', 'reason']
