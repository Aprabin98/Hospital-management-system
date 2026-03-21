from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    # Doctor
    path('write/<int:appointment_id>/', views.write_prescription, name='write_prescription'),
    path('<int:pk>/edit/', views.edit_prescription, name='edit_prescription'),
    path('my-prescriptions/', views.doctor_prescriptions, name='doctor_prescriptions'),

    # Patient
    path('my/', views.patient_prescriptions, name='patient_prescriptions'),

    # Both
    path('<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('<int:pk>/download/', views.download_prescription_pdf, name='download_pdf'),
]