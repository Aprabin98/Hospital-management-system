from django.urls import path
from . import views
from no_show_predictor.views import predict_no_show_risk
from . import feature_views
from . import queue_api_views

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
    path('waiting-list/queue/', feature_views.waiting_list_queue, name='waiting_list_queue'),
    path('waiting-list/<int:waiting_id>/promote/', feature_views.manual_promote_waiting, name='manual_promote_waiting'),
    path('waiting-list/<int:waiting_id>/priority/', feature_views.set_waiting_priority, name='set_waiting_priority'),

    # No-show advanced workflow
    path('no-show/dashboard/', feature_views.no_show_risk_dashboard, name='no_show_risk_dashboard'),
    path('no-show/<int:appointment_id>/outcome/', feature_views.set_no_show_outcome, name='set_no_show_outcome'),

    # AI triage workflow
    path('triage/', views.triage_dashboard, name='triage_dashboard'),
    path('report-reader/', views.report_reader_dashboard, name='report_reader_dashboard'),
    path('report-reader/<int:analysis_id>/', views.report_reader_detail, name='report_reader_detail'),

    # API
    path('api/slots/', views.get_slots_api, name='get_slots_api'),
    path('api/no-show-risk/', predict_no_show_risk, name='predict_no_show_api'),
    
    # Phase 2: Queue Management APIs
    path('api/queue/', queue_api_views.queue_list_api, name='queue_list_api'),
    path('api/queue/<int:queue_id>/status/', queue_api_views.queue_update_status_api, name='queue_update_status_api'),
    path('api/queue/check-duplicate/', queue_api_views.check_duplicate_patient_api, name='check_duplicate_api'),
    path('api/queue/<int:queue_id>/rebook/', queue_api_views.no_show_rebook_api, name='no_show_rebook_api'),
]