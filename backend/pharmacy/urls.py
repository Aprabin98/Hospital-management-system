from django.urls import path
from . import api_views

urlpatterns = [
    # Medication Inventory
    path('medications/', api_views.medication_inventory_api, name='medication_inventory_list'),
    path('medications/<int:medication_id>/', api_views.medication_detail_api, name='medication_detail'),
    
    # Dispensing Queue & Transactions
    path('pending-dispense/', api_views.pending_dispense_queue_api, name='pending_dispense_queue'),
    path('dispense-transaction/', api_views.dispense_transaction_api, name='dispense_transaction_create'),
    path('dispense-transaction/<int:transaction_id>/', api_views.dispense_transaction_api, name='dispense_transaction_update'),
    
    # Controlled Drugs
    path('controlled-drugs/', api_views.controlled_drug_log_api, name='controlled_drug_log'),
    
    # Alerts
    path('alerts/', api_views.pharmacy_alerts_api, name='pharmacy_alerts'),
    
    # Dashboard
    path('dashboard/', api_views.pharmacy_dashboard_api, name='pharmacy_dashboard'),
]
