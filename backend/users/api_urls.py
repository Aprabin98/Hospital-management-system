"""API URL patterns for authentication and users"""
from django.urls import path
from . import api_views
from . import admin_api_views
from appointments import api_views as appointments_api_views
from clinical import api_views as clinical_api_views
from lab import api_views as lab_api_views
from prescriptions import api_views as prescriptions_api_views
from rooms import api_views as rooms_api_views
from heart_risk import api_views as heart_risk_api_views
from notifications import api_views as notifications_api_views
from reviews import api_views as reviews_api_views
from payments import api_views as payments_api_views
from audit import api_views as audit_api_views
from audit import health_views
from drug_checker import api_views as drug_checker_api_views

app_name = 'api'

urlpatterns = [
    # Authentication
    path('auth/login/', api_views.login_api, name='login'),
    path('auth/2fa-verify/', api_views.two_factor_verify_api, name='two_factor_verify'),
    path('auth/2fa-resend/', api_views.two_factor_resend_api, name='two_factor_resend'),
    path('auth/logout/', api_views.logout_api, name='logout'),
    path('auth/register/', api_views.register_api, name='register'),
    path('auth/password-reset/request/', api_views.password_reset_request_api, name='password_reset_request'),
    path('auth/password-reset/confirm/', api_views.password_reset_confirm_api, name='password_reset_confirm'),
    path('auth/me/', api_views.current_user_api, name='current_user'),
    
    # Profile
    path('profile/', api_views.profile_edit_api, name='profile_edit'),
    
    # Dashboard
    path('dashboard/stats/', api_views.dashboard_stats_api, name='dashboard_stats'),
    path('security/login-attempts/', api_views.login_attempts_admin_api, name='login_attempts_admin'),
    
    # Admin User Management
    path('users/', admin_api_views.users_list_api, name='users_list'),
    path('users/<int:user_id>/', admin_api_views.user_detail_api, name='user_detail'),
    path('users/stats/', admin_api_views.user_stats_api, name='user_stats'),
    
    # Patients
    path('patients/', api_views.patients_list_api, name='patients_list'),
    path('patients/<int:patient_id>/', api_views.patient_detail_api, name='patient_detail'),
    
    # Appointments
    path('appointments/', appointments_api_views.appointments_list_api, name='appointments_list'),
    path('appointments/<int:appointment_id>/', appointments_api_views.appointment_detail_api, name='appointment_detail'),
    path('appointments/create/', appointments_api_views.appointment_create_api, name='appointment_create'),
    path('appointments/<int:appointment_id>/update/', appointments_api_views.appointment_update_api, name='appointment_update'),
    path('appointments/available-slots/', appointments_api_views.appointments_available_slots_api, name='appointments_available_slots'),
    path('appointments/<int:appointment_id>/download-pdf/', appointments_api_views.appointment_download_pdf_api, name='appointment_download_pdf'),
    
    # Medical Records
    path('medical-records/', clinical_api_views.medical_records_list_api, name='medical_records_list'),
    path('medical-records/<int:record_id>/', clinical_api_views.medical_record_detail_api, name='medical_record_detail'),
    path('medical-records/create/', clinical_api_views.medical_record_create_api, name='medical_record_create'),
    path('medical-records/<int:record_id>/update/', clinical_api_views.medical_record_update_api, name='medical_record_update'),
    
    # Vital Logs
    path('vital-logs/', clinical_api_views.vital_logs_list_api, name='vital_logs_list'),
    
    # Doctors
    path('doctors/', clinical_api_views.doctors_list_api, name='doctors_list'),
    path('doctors/create/', clinical_api_views.doctor_create_api, name='doctor_create'),
    path('doctors/<int:doctor_id>/', clinical_api_views.doctor_detail_api, name='doctor_detail'),
    path('doctor-leaves/', clinical_api_views.doctor_leaves_api, name='doctor_leaves'),
    path('doctor-leaves/<int:leave_id>/', clinical_api_views.doctor_leave_detail_api, name='doctor_leave_detail'),
    path('doctor-leaves/admin/', clinical_api_views.doctor_leaves_admin_api, name='doctor_leaves_admin'),
    path('doctor-leaves/<int:leave_id>/review/', clinical_api_views.doctor_leave_review_api, name='doctor_leave_review'),
    path('specializations/', clinical_api_views.specializations_list_create_api, name='specializations_list_create'),
    path('specializations/<int:specialization_id>/', clinical_api_views.specialization_detail_api, name='specialization_detail'),
    path('shifts/', clinical_api_views.shifts_list_create_api, name='shifts_list_create'),
    path('shifts/<int:shift_id>/', clinical_api_views.shift_detail_api, name='shift_detail'),
    path('schedules/', clinical_api_views.schedules_list_create_api, name='schedules_list_create'),
    path('schedules/<int:schedule_id>/', clinical_api_views.schedule_detail_api, name='schedule_detail'),
    
    # Lab Tests
    path('lab/tests/', lab_api_views.lab_tests_list_api, name='lab_tests_list'),
    path('lab/bookings/', lab_api_views.lab_bookings_list_api, name='lab_bookings_list'),
    path('lab/bookings/create/', lab_api_views.lab_booking_create_api, name='lab_booking_create'),
    path('lab/bookings/<int:booking_id>/', lab_api_views.lab_booking_detail_api, name='lab_booking_detail'),
    path('lab/results/', lab_api_views.lab_results_list_api, name='lab_results_list'),
    path('lab/results/<int:result_id>/', lab_api_views.lab_result_detail_api, name='lab_result_detail'),
    path('lab/recommendations/', lab_api_views.lab_recommendations_list_api, name='lab_recommendations_list'),
    path('lab/recommendations/create/', lab_api_views.lab_recommendation_create_api, name='lab_recommendation_create'),
    path('lab/templates/', lab_api_views.lab_templates_admin_api, name='lab_templates_admin'),
    path('lab/templates/<int:template_id>/', lab_api_views.lab_template_admin_detail_api, name='lab_template_admin_detail'),
    path('lab/templates/<int:template_id>/fields/', lab_api_views.lab_template_fields_api, name='lab_template_fields'),
    path('lab/template-fields/<int:field_id>/', lab_api_views.lab_template_field_detail_api, name='lab_template_field_detail'),
    path('lab/templates/<int:template_id>/schedules/', lab_api_views.lab_template_schedules_api, name='lab_template_schedules'),
    path('lab/template-schedules/<int:schedule_id>/', lab_api_views.lab_template_schedule_detail_api, name='lab_template_schedule_detail'),
    path('lab/admin/bookings/', lab_api_views.lab_admin_bookings_api, name='lab_admin_bookings'),
    path('lab/results/<int:result_id>/verify/', lab_api_views.lab_verify_result_api, name='lab_result_verify'),
    path('lab/results/<int:result_id>/release/', lab_api_views.lab_release_result_api, name='lab_result_release'),
    
    # Prescriptions
    path('prescriptions/', prescriptions_api_views.prescriptions_list_api, name='prescriptions_list'),
    path('prescriptions/create/', prescriptions_api_views.prescription_create_api, name='prescriptions_create'),
    path('prescriptions/<int:prescription_id>/', prescriptions_api_views.prescription_detail_api, name='prescription_detail'),
    path('prescriptions/<int:prescription_id>/update/', prescriptions_api_views.prescription_update_api, name='prescription_update'),
    path('prescriptions/<int:prescription_id>/download-pdf/', prescriptions_api_views.prescription_download_pdf_api, name='prescription_download_pdf'),
    path('prescriptions/active/', prescriptions_api_views.prescriptions_active_api, name='prescriptions_active'),
    
    # Rooms
    path('rooms/available/', rooms_api_views.rooms_available_api, name='rooms_available'),
    path('rooms/create/', rooms_api_views.room_create_api, name='room_create'),
    path('rooms/assignments/', rooms_api_views.room_assignments_list_api, name='room_assignments_list'),
    path('rooms/current-assignment/', rooms_api_views.room_current_assignment_api, name='room_current_assignment'),
    path('rooms/admission-requests/', rooms_api_views.admission_requests_list_api, name='admission_requests_list'),
    path('rooms/admission-requests/admin/', rooms_api_views.admission_requests_admin_api, name='admission_requests_admin'),
    path('rooms/admission-requests/<int:request_id>/review/', rooms_api_views.admission_request_review_api, name='admission_request_review'),
    path('rooms/book-bed/', rooms_api_views.room_book_bed_api, name='room_book_bed'),
    path('rooms/book-request/', rooms_api_views.room_book_request_api, name='room_book_request'),
    path('rooms/transfers/', rooms_api_views.room_transfers_admin_api, name='room_transfers_admin'),
    path('rooms/transfers/create/', rooms_api_views.room_transfer_create_api, name='room_transfer_create'),
    path('rooms/transfers/<int:transfer_id>/review/', rooms_api_views.room_transfer_review_api, name='room_transfer_review'),

    # Notifications
    path('notifications/', notifications_api_views.notifications_list_api, name='notifications_list'),
    path('notifications/unread-count/', notifications_api_views.notifications_unread_count_api, name='notifications_unread_count'),
    path('notifications/mark-all-read/', notifications_api_views.notifications_mark_all_read_api, name='notifications_mark_all_read'),
    path('notifications/<int:notification_id>/mark-read/', notifications_api_views.notification_mark_read_api, name='notifications_mark_read'),
    path('notifications/<int:notification_id>/', notifications_api_views.notification_delete_api, name='notifications_delete'),

    # Reviews
    path('reviews/', reviews_api_views.reviews_api, name='reviews_api'),

    # Audit Logs
    path('audit/logs/', audit_api_views.audit_logs_list_api, name='audit_logs_list'),

    # Drug Interactions (Admin)
    path('drug-interactions/', drug_checker_api_views.drug_interactions_list_create_api, name='drug_interactions_list_create'),
    path('drug-interactions/<int:interaction_id>/', drug_checker_api_views.drug_interaction_detail_api, name='drug_interaction_detail'),
    
    # Payments & Billing
    path('payments/', payments_api_views.payments_list_api, name='payments_list'),
    path('payments/<int:payment_id>/', payments_api_views.payment_detail_api, name='payment_detail'),
    path('payments/stats/', payments_api_views.payment_stats_api, name='payment_stats'),
    path('payments/revenue/', payments_api_views.payment_revenue_summary_api, name='payment_revenue_summary'),
    path('payments/<int:payment_id>/mark-paid/', payments_api_views.payment_mark_paid_api, name='payment_mark_paid'),
    path('payments/<int:payment_id>/refund/', payments_api_views.refund_request_api, name='refund_request'),
    path('payments/<int:payment_id>/refund/manage/', payments_api_views.refund_manage_api, name='refund_manage'),
    path('payments/<int:payment_id>/invoice/', payments_api_views.invoice_download_api, name='invoice_download'),
    path('payments/insurance/', payments_api_views.insurance_list_api, name='insurance_list'),
    path('payments/insurance/create/', payments_api_views.insurance_create_api, name='insurance_create'),
    path('payments/insurance/<int:insurance_id>/verify/', payments_api_views.insurance_verify_api, name='insurance_verify'),
    path('payments/refunds/admin/', payments_api_views.refunds_admin_api, name='refunds_admin'),

    # Waiting-list and no-show operations
    path('appointments/waiting-list/queue/', appointments_api_views.waiting_list_queue_api, name='appointments_waiting_list_queue'),
    path('appointments/waiting-list/<int:waiting_id>/promote/', appointments_api_views.waiting_list_promote_api, name='appointments_waiting_list_promote'),
    path('appointments/waiting-list/<int:waiting_id>/priority/', appointments_api_views.waiting_list_priority_api, name='appointments_waiting_list_priority'),
    path('appointments/no-show/dashboard/', appointments_api_views.no_show_dashboard_api, name='appointments_no_show_dashboard'),
    path('appointments/no-show/<int:appointment_id>/outcome/', appointments_api_views.no_show_outcome_api, name='appointments_no_show_outcome'),

    # Room statistics workflow
    path('rooms/statistics/', rooms_api_views.room_statistics_api, name='rooms_statistics'),
    path('rooms/statistics/export/csv/', rooms_api_views.room_statistics_export_csv_api, name='rooms_statistics_export_csv'),
    
    # Heart Risk Assessment  
    path('heart-risk/', heart_risk_api_views.heart_risk_assessments_list_api, name='heart_risk_assessments_list'),
    path('heart-risk/latest/', heart_risk_api_views.heart_risk_latest_api, name='heart_risk_latest'),
    path('heart-risk/assess/', heart_risk_api_views.heart_risk_assessment_create_api, name='heart_risk_assessment_create'),
    path('heart-risk/<int:assessment_id>/', heart_risk_api_views.heart_risk_assessment_detail_api, name='heart_risk_detail'),

    # AI Report Reader
    path('ai-report-reader/', appointments_api_views.report_reader_list_api, name='ai_report_reader_list'),
    path('ai-report-reader/create/', appointments_api_views.report_reader_create_api, name='ai_report_reader_create'),
    path('ai-report-reader/<int:analysis_id>/', appointments_api_views.report_reader_detail_api, name='ai_report_reader_detail'),
    path('ai-triage/', appointments_api_views.ai_triage_api, name='ai_triage'),

    # System Health Check & Monitoring (Phase 1)
    path('system/health-check/', health_views.system_health_check, name='system_health_check'),
    path('system/health/', health_views.system_health_check, name='system_health'),
    path('system/queue-metrics/', health_views.system_queue_metrics, name='system_queue_metrics'),
    path('system/api-metrics/', health_views.system_api_metrics, name='system_api_metrics'),
    path('rbac/role-matrix/', health_views.rbac_role_matrix, name='rbac_role_matrix'),
    path('system/security-status/', health_views.system_security_status, name='system_security_status'),
]
