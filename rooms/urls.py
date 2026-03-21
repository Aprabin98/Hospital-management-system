from django.urls import path

from . import views

app_name = 'rooms'

urlpatterns = [
    path('', views.room_list, name='room_list'),
    path('create/', views.room_create, name='room_create'),
    path('<int:pk>/', views.room_detail, name='room_detail'),
    path('<int:pk>/edit/', views.room_edit, name='room_edit'),
    path('<int:room_pk>/bed/<int:bed_pk>/edit/', views.room_bed_edit, name='room_bed_edit'),
    path('admit/', views.admit_patient, name='admit_patient'),
    path('assignments/active/', views.active_assignments, name='active_assignments'),
    path('assignments/<int:pk>/discharge/', views.discharge_patient, name='discharge_patient'),
]
