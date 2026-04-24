from django.urls import path

from . import api_views

app_name = 'radiology'

urlpatterns = [
    path('catalog/', api_views.imaging_catalog_list_create_api, name='catalog_list_create'),
    path('orders/', api_views.imaging_orders_list_create_api, name='orders_list_create'),
    path('orders/<int:order_id>/', api_views.imaging_order_detail_api, name='order_detail'),
    path('orders/<int:order_id>/report/', api_views.imaging_order_report_api, name='order_report'),
    path('orders/<int:order_id>/release/', api_views.imaging_order_release_api, name='order_release'),
    path('orders/<int:order_id>/attachments/', api_views.imaging_order_attachments_api, name='order_attachments'),
    path('worklist/', api_views.imaging_worklist_api, name='worklist'),
    path('history/', api_views.imaging_history_api, name='history'),
]
