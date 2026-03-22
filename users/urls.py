from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('2fa/verify/', views.two_factor_verify, name='two_factor_verify'),
    path('2fa/resend/', views.two_factor_resend, name='two_factor_resend'),
    path('logout/', views.logout_view, name='logout'),

    # Email Activation
    path('activate/<int:user_id>/<str:token>/', views.activate_account, name='activate'),

    # Dashboards
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/patient/', views.patient_dashboard, name='patient_dashboard'),
    path('dashboard/doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/receptionist/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('lab-dashboard/', views.lab_technician_dashboard, name='lab_technician_dashboard'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Password Reset
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('reset-password/<int:user_id>/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
]