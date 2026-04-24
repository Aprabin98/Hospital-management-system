from django.contrib import admin

from .models import ImagingAttachment, ImagingCatalog, ImagingOrder, ImagingReport


@admin.register(ImagingCatalog)
class ImagingCatalogAdmin(admin.ModelAdmin):
    list_display = ('name', 'modality', 'price', 'turnaround_hours', 'is_active')
    list_filter = ('modality', 'is_active')
    search_fields = ('name', 'description')


@admin.register(ImagingOrder)
class ImagingOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'catalog_item', 'priority', 'status', 'created_at')
    list_filter = ('priority', 'status', 'catalog_item__modality')
    search_fields = ('patient__full_name', 'catalog_item__name')


@admin.register(ImagingReport)
class ImagingReportAdmin(admin.ModelAdmin):
    list_display = ('order', 'report_status', 'is_critical', 'reported_by', 'released_at')
    list_filter = ('report_status', 'is_critical')
    search_fields = ('order__patient__full_name', 'impression')


@admin.register(ImagingAttachment)
class ImagingAttachmentAdmin(admin.ModelAdmin):
    list_display = ('order', 'file_name', 'mime_type', 'size_bytes', 'created_at')
    search_fields = ('order__patient__full_name', 'file_name', 'file_url')
