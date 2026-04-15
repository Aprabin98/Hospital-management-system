from django.urls import path

from . import views

app_name = 'rooms'

urlpatterns = [
    # Admin/Receptionist - Room Management
    path('', views.room_list, name='room_list'),
    path('create/', views.room_create, name='room_create'),
    path('<int:pk>/', views.room_detail, name='room_detail'),
    path('<int:pk>/edit/', views.room_edit, name='room_edit'),
    path('<int:room_pk>/bed/<int:bed_pk>/edit/', views.room_bed_edit, name='room_bed_edit'),
    path('admit/', views.admit_patient, name='admit_patient'),
    path('assignments/active/', views.active_assignments, name='active_assignments'),
    path('assignments/<int:pk>/discharge/', views.discharge_patient, name='discharge_patient'),
    
    # Role-Based Dashboard
    path('dashboard/', views.room_dashboard, name='room_dashboard'),
    
    # Patient Routes
    path('patient/available/', views.patient_available_rooms, name='patient_available_rooms'),
    path('patient/book/', views.patient_book_room, name='patient_book_room'),
    
    # Doctor Routes
    path('doctor/patients/', views.doctor_patient_transfers, name='doctor_patient_transfers'),
    path('doctor/transfer/', views.doctor_transfer_patient, name='doctor_transfer_patient'),
    path('doctor/admission-requests/', views.doctor_admission_requests, name='doctor_admission_requests'),
    
    # Receptionist Routes
    path('receptionist/assign/', views.receptionist_assign_room, name='receptionist_assign_room'),
    path('receptionist/patient-search/', views.receptionist_patient_search, name='receptionist_patient_search'),
    path('receptionist/requests/<int:pk>/reject/', views.receptionist_reject_admission_request, name='receptionist_reject_admission_request'),
    path('receptionist/occupancy/', views.receptionist_occupancy, name='receptionist_occupancy'),
    
    # Admin Routes
    path('statistics/', views.room_statistics, name='room_statistics'),
    path('statistics/export/csv/', views.room_statistics_export_csv, name='room_statistics_export_csv'),
    
    # API Routes - Real-time Occupancy
    path('api/availability/', views.api_room_availability, name='api_room_availability'),
    path('api/rooms/<int:room_id>/beds/', views.api_room_beds_availability, name='api_room_beds_availability'),
    path('api/patient/assignments/', views.api_patient_room_assignments, name='api_patient_room_assignments'),
    path('api/doctor/occupancy/', views.api_doctor_patient_occupancy, name='api_doctor_patient_occupancy'),
    path('api/receptionist/bed-status/', views.api_receptionist_bed_status, name='api_receptionist_bed_status'),
]
