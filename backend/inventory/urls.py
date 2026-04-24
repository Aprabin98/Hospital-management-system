from django.urls import path

from . import api_views

app_name = 'inventory'

urlpatterns = [
    path('categories/', api_views.inventory_categories_api, name='categories'),
    path('items/', api_views.inventory_items_api, name='items'),
    path('vendors/', api_views.inventory_vendors_api, name='vendors'),
    path('purchase-orders/', api_views.inventory_purchase_orders_api, name='purchase_orders'),
    path('purchase-orders/<int:order_id>/receive/', api_views.inventory_purchase_order_receive_api, name='purchase_order_receive'),
    path('stock-movements/', api_views.inventory_stock_movements_api, name='stock_movements'),
    path('dashboard/', api_views.inventory_dashboard_api, name='dashboard'),
]
