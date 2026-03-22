from django.urls import path

from . import views

app_name = 'drug_checker'

urlpatterns = [
    path('api/check-interactions/', views.check_interactions, name='check_interactions'),
]
