from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Patient
    path('my/', views.patient_payments, name='patient_payments'),
    path('<int:pk>/', views.payment_detail, name='payment_detail'),
    path('<int:pk>/download-receipt/', views.download_receipt, name='download_receipt'),
    path('<int:pk>/refund/', views.request_refund, name='request_refund'),

    # Admin / Receptionist
    path('all/', views.admin_payments, name='admin_payments'),
    path('<int:pk>/mark-paid/', views.mark_paid, name='mark_paid'),
    path('refund/<int:pk>/manage/', views.manage_refund, name='manage_refund'),
    path('revenue/', views.revenue_summary, name='revenue_summary'),
]