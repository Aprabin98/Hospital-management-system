from django.urls import path
from . import views
from . import analytics_views

app_name = 'clinical'

urlpatterns = [
    # Specializations (Admin)
    path('specializations/', views.specialization_list, name='specialization_list'),
    path('specializations/<int:pk>/edit/', views.specialization_edit, name='specialization_edit'),
    path('specializations/<int:pk>/delete/', views.specialization_delete, name='specialization_delete'),

    # Shifts (Admin)
    path('shifts/', views.shift_list, name='shift_list'),
    path('shifts/<int:pk>/edit/', views.shift_edit, name='shift_edit'),
    path('shifts/<int:pk>/delete/', views.shift_delete, name='shift_delete'),

    # Doctors (Admin)
    path('doctors/', views.doctor_list_admin, name='doctor_list_admin'),
    path('doctors/create/', views.doctor_create, name='doctor_create'),
    path('doctors/<int:pk>/edit/', views.doctor_edit, name='doctor_edit'),
    path('doctors/<int:pk>/delete/', views.doctor_delete, name='doctor_delete'),

    # Schedules (Admin)
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),

    # Doctor Leave (Doctor)
    path('my-leaves/', views.doctor_leave, name='doctor_leave'),
    path('my-leaves/<int:pk>/edit/', views.doctor_leave_edit, name='doctor_leave_edit'),
    path('my-leaves/<int:pk>/delete/', views.doctor_leave_delete, name='doctor_leave_delete'),

    # Public (Patient)
    path('find-doctors/', views.doctor_search, name='doctor_search'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),

    # Doctor (Own Profile)
    path('my-profile/', views.doctor_edit_own_profile, name='doctor_edit_own_profile'),

    # Analytics and performance
    path('analytics/dashboard/', analytics_views.hospital_analytics_dashboard, name='hospital_analytics_dashboard'),
    path('analytics/doctor-metrics/', analytics_views.doctor_performance_metrics, name='doctor_performance_metrics'),
]