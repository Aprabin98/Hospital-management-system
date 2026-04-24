from rest_framework import serializers

from .models import (
    InventoryCategory,
    InventoryItem,
    PurchaseOrder,
    PurchaseOrderLine,
    StockMovement,
    Vendor,
)


class InventoryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCategory
        fields = ['id', 'name', 'description']


class InventoryItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'category', 'category_name', 'name', 'sku', 'unit',
            'current_stock', 'reorder_level', 'expiry_date', 'is_active',
            'is_low_stock', 'updated_at',
        ]


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'contact_phone', 'contact_email', 'address', 'is_active']


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = ['id', 'item', 'item_name', 'quantity', 'unit_price', 'received_quantity']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    lines = PurchaseOrderLineSerializer(many=True, required=False)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'vendor', 'vendor_name', 'ordered_by', 'status', 'order_date', 'expected_date', 'total_amount', 'created_at', 'lines']
        read_only_fields = ['ordered_by', 'created_at']


class StockMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        model = StockMovement
        fields = ['id', 'item', 'item_name', 'movement_type', 'quantity', 'reference', 'notes', 'performed_by', 'created_at']
        read_only_fields = ['performed_by', 'created_at']
