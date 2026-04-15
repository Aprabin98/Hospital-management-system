from django.urls import path
from . import views

app_name = 'lab'

urlpatterns = [
    # Admin - Template Management
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    path('templates/<int:pk>/fields/', views.template_fields, name='template_fields'),
    path('templates/<int:pk>/schedule/', views.template_schedule, name='template_schedule'),
    path('fields/<int:pk>/delete/', views.field_delete, name='field_delete'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),

    # Admin - Bookings
    path('admin/bookings/', views.admin_bookings, name='admin_bookings'),
    path('results/<int:pk>/verify/', views.verify_result, name='verify_result'),
    path('results/<int:pk>/release/', views.release_result, name='release_result'),

    # Patient
    path('tests/', views.test_list, name='test_list'),
    path('tests/<int:pk>/', views.test_detail, name='test_detail'),
    path('tests/<int:pk>/book/', views.book_test, name='book_test'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),

    # Lab Technician
    path('lab-dashboard/', views.lab_dashboard, name='lab_dashboard'),
    path('bookings/<int:booking_id>/fill-result/', views.fill_result, name='fill_result'),
    path('results/<int:pk>/update/', views.update_result, name='update_result'),

    # Download
    path('results/<int:pk>/download/', views.download_report, name='download_report'),
    # Lab Technician Status Update
    path('bookings/<int:pk>/update-status/', views.update_booking_status, name='update_booking_status'),

    # Doctor views patient reports
    path('patient/<int:patient_id>/reports/', views.patient_reports_for_doctor, name='patient_reports'),
]