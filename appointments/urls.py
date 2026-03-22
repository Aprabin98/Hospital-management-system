from django.urls import path
from . import views
from no_show_predictor.views import predict_no_show_risk

app_name = 'appointments'

urlpatterns = [
    # Booking Flow (4 steps)
    path('book/step1/', views.book_step1, name='book_step1'),
    path('book/step2/', views.book_step2, name='book_step2'),
    path('book/step3/', views.book_step3, name='book_step3'),
    path('book/step4/', views.book_step4, name='book_step4'),

    # Appointment Management
    path('', views.appointment_list, name='appointment_list'),
    path('<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('<int:pk>/complete/', views.complete_appointment, name='complete_appointment'),
    path('<int:pk>/download-pdf/', views.download_pdf, name='download_pdf'),

    # Doctor views
    path('today/', views.todays_appointments, name='todays_appointments'),

    # Waiting List
    path('waiting-list/<int:doctor_id>/<str:date_str>/', views.join_waiting_list, name='join_waiting_list'),

    # API
    path('api/slots/', views.get_slots_api, name='get_slots_api'),
    path('api/no-show-risk/', predict_no_show_risk, name='predict_no_show_api'),
]