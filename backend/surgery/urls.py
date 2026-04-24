from django.urls import path

from . import api_views

app_name = 'surgery'

urlpatterns = [
    path('schedules/', api_views.ot_schedule_list_create_api, name='schedule_list_create'),
    path('schedules/<int:schedule_id>/', api_views.ot_schedule_detail_api, name='schedule_detail'),
    path('schedules/<int:schedule_id>/procedure-note/', api_views.ot_procedure_note_api, name='procedure_note'),
    path('schedules/<int:schedule_id>/post-op-notes/', api_views.ot_post_op_notes_api, name='post_op_notes'),
    path('dashboard/', api_views.ot_dashboard_api, name='dashboard'),
]
