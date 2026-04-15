from django.urls import path

from . import views

app_name = 'drug_checker'

urlpatterns = [
    path('api/check-interactions/', views.check_interactions, name='check_interactions'),
    path('manage/', views.manage_interactions, name='manage_interactions'),
    path('manage/<int:pk>/toggle-status/', views.toggle_interaction_status, name='toggle_interaction_status'),
]
