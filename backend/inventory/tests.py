from rest_framework import status
from rest_framework.test import APITestCase

from inventory.models import InventoryCategory, InventoryItem, PurchaseOrder, PurchaseOrderLine, StockMovement, Vendor
from users.models import User


class InventoryApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='inv.admin@example.com', username='inv_admin', password='pass1234', role='ADMIN', is_active=True)
        self.pharmacist = User.objects.create_user(email='inv.pharm@example.com', username='inv_pharm', password='pass1234', role='PHARMACIST', is_active=True)
        self.patient = User.objects.create_user(email='inv.patient@example.com', username='inv_patient', password='pass1234', role='PATIENT', is_active=True)

        self.category = InventoryCategory.objects.create(name='Consumables')

    def test_pharmacist_can_create_inventory_item(self):
        self.client.force_authenticate(user=self.pharmacist)
        response = self.client.post('/api/inventory/items/', {
            'category': self.category.id,
            'name': 'Syringe 5ml',
            'sku': 'CONS-0001',
            'unit': 'pcs',
            'current_stock': '20',
            'reorder_level': '10',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_low_stock_filter(self):
        InventoryItem.objects.create(category=self.category, name='Cannula', sku='CONS-0002', unit='pcs', current_stock=2, reorder_level=5)
        InventoryItem.objects.create(category=self.category, name='Tape', sku='CONS-0003', unit='pcs', current_stock=50, reorder_level=5)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/inventory/items/?low_stock=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_receive_purchase_order_updates_stock(self):
        item = InventoryItem.objects.create(category=self.category, name='Gloves', sku='CONS-0004', unit='box', current_stock=5, reorder_level=5)
        vendor = Vendor.objects.create(name='Medi Supplies')
        po = PurchaseOrder.objects.create(vendor=vendor, ordered_by=self.admin, status='PLACED')
        PurchaseOrderLine.objects.create(purchase_order=po, item=item, quantity=10, unit_price=100)

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'/api/inventory/purchase-orders/{po.id}/receive/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        item.refresh_from_db()
        po.refresh_from_db()
        self.assertEqual(float(item.current_stock), 15.0)
        self.assertEqual(po.status, 'RECEIVED')
        self.assertTrue(StockMovement.objects.filter(item=item, movement_type='RECEIPT').exists())
