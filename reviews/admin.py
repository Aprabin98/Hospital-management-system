from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'rating', 'appointment', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['patient__full_name', 'doctor__user__username', 'comment']
