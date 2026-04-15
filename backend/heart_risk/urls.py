from django.urls import path

from . import views

app_name = 'heart_risk'

urlpatterns = [
    path('assess/', views.assess_heart_risk, name='assess'),
    path('api/search-patients/', views.search_patients, name='search_patients'),
]
