from django.contrib import admin

from .models import InventoryCategory, InventoryItem, PurchaseOrder, PurchaseOrderLine, StockMovement, Vendor


@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sku', 'current_stock', 'reorder_level', 'expiry_date', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku')


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'contact_phone', 'is_active')


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'status', 'order_date', 'expected_date', 'total_amount')
    list_filter = ('status',)
    inlines = [PurchaseOrderLineInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'movement_type', 'quantity', 'reference', 'created_at')
    list_filter = ('movement_type',)
