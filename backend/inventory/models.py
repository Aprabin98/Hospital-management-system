from django.db import models
from django.utils import timezone


class InventoryCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    category = models.ForeignKey(InventoryCategory, on_delete=models.PROTECT, related_name='items')
    name = models.CharField(max_length=180)
    sku = models.CharField(max_length=80, unique=True)
    unit = models.CharField(max_length=30, default='unit')
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    @property
    def is_low_stock(self):
        return self.current_stock <= self.reorder_level

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Vendor(models.Model):
    name = models.CharField(max_length=180, unique=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PLACED', 'Placed'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='purchase_orders')
    ordered_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    order_date = models.DateField(default=timezone.localdate)
    expected_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name='purchase_lines')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    received_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class StockMovement(models.Model):
    MOVEMENT_CHOICES = [
        ('RECEIPT', 'Receipt'),
        ('ISSUE', 'Issue'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
