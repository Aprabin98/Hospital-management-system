from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('my/', views.my_reviews, name='my_reviews'),
    path('doctor/<int:doctor_id>/', views.doctor_reviews, name='doctor_reviews'),
    path('create/<int:appointment_id>/', views.create_review, name='create_review'),
]
