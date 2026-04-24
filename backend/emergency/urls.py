from django.urls import path

from . import api_views

app_name = 'emergency'

urlpatterns = [
    path('encounters/', api_views.emergency_encounter_list_create_api, name='encounter_list_create'),
    path('encounters/<int:encounter_id>/', api_views.emergency_encounter_detail_api, name='encounter_detail'),
    path('triage-queue/', api_views.emergency_triage_queue_api, name='triage_queue'),
    path('encounters/<int:encounter_id>/triage/', api_views.emergency_triage_records_api, name='triage_records'),
    path('encounters/<int:encounter_id>/notes/', api_views.emergency_notes_api, name='encounter_notes'),
]
