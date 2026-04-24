from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .api_serializers import (
    InventoryCategorySerializer,
    InventoryItemSerializer,
    PurchaseOrderSerializer,
    StockMovementSerializer,
    VendorSerializer,
)
from .models import InventoryCategory, InventoryItem, PurchaseOrder, PurchaseOrderLine, StockMovement, Vendor


def _has_inventory_role(user):
    return bool(user and user.is_authenticated and user.role in ['ADMIN', 'PHARMACIST'])


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def inventory_categories_api(request):
    if not _has_inventory_role(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    if request.method == 'GET':
        return Response(InventoryCategorySerializer(InventoryCategory.objects.all(), many=True).data)
    serializer = InventoryCategorySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def inventory_items_api(request):
    if not _has_inventory_role(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        queryset = InventoryItem.objects.select_related('category').all()
        if request.query_params.get('low_stock') == 'true':
            queryset = [item for item in queryset if item.is_low_stock]
            return Response(InventoryItemSerializer(queryset, many=True).data)
        return Response(InventoryItemSerializer(queryset, many=True).data)

    serializer = InventoryItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def inventory_vendors_api(request):
    if not _has_inventory_role(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response(VendorSerializer(Vendor.objects.all(), many=True).data)

    serializer = VendorSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def inventory_purchase_orders_api(request):
    if not _has_inventory_role(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        queryset = PurchaseOrder.objects.select_related('vendor', 'ordered_by').prefetch_related('lines__item').all()
        return Response(PurchaseOrderSerializer(queryset, many=True).data)

    serializer = PurchaseOrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order = serializer.save(ordered_by=request.user)

    lines = request.data.get('lines', [])
    total_amount = Decimal('0')
    for line in lines:
        qty = Decimal(str(line.get('quantity', '0')))
        unit_price = Decimal(str(line.get('unit_price', '0')))
        PurchaseOrderLine.objects.create(
            purchase_order=order,
            item_id=line.get('item'),
            quantity=qty,
            unit_price=unit_price,
        )
        total_amount += (qty * unit_price)

    if lines:
        order.status = 'PLACED'
        order.total_amount = total_amount
        order.save(update_fields=['status', 'total_amount'])

    refreshed = PurchaseOrder.objects.select_related('vendor', 'ordered_by').prefetch_related('lines__item').get(id=order.id)
    return Response(PurchaseOrderSerializer(refreshed).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inventory_purchase_order_receive_api(request, order_id):
    if not _has_inventory_role(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    order = get_object_or_404(PurchaseOrder.objects.prefetch_related('lines__item'), id=order_id)
    if order.status not in ['PLACED', 'DRAFT']:
        return Response({'detail': f'Order cannot be received in {order.status} state.'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        for line in order.lines.select_related('item').all():
            line.received_quantity = line.quantity
            line.save(update_fields=['received_quantity'])

            InventoryItem.objects.filter(id=line.item_id).update(current_stock=F('current_stock') + line.quantity)
            StockMovement.objects.create(
                item_id=line.item_id,
                movement_type='RECEIPT',
                quantity=line.quantity,
                reference=f'PO-{order.id}',
                notes='Purchase order receipt',
                performed_by=request.user,
            )

        order.status = 'RECEIVED'
        order.expected_date = order.expected_date or timezone.localdate()
        order.save(update_fields=['status', 'expected_date'])

    refreshed = PurchaseOrder.objects.select_related('vendor', 'ordered_by').prefetch_related('lines__item').get(id=order.id)
    return Response(PurchaseOrderSerializer(refreshed).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_stock_movements_api(request):
    if not _has_inventory_role(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    movements = StockMovement.objects.select_related('item', 'performed_by').all()[:200]
    return Response(StockMovementSerializer(movements, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_dashboard_api(request):
    if not _has_inventory_role(request.user):
        return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

    items = InventoryItem.objects.filter(is_active=True)
    low_stock = [item.id for item in items if item.is_low_stock]
    expiring_soon = items.filter(expiry_date__isnull=False, expiry_date__lte=timezone.localdate() + timezone.timedelta(days=30)).count()

    return Response({
        'total_items': items.count(),
        'low_stock_items': len(low_stock),
        'expiring_within_30_days': expiring_soon,
        'open_purchase_orders': PurchaseOrder.objects.filter(status__in=['DRAFT', 'PLACED']).count(),
    })
