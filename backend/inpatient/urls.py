from django.urls import path

from . import api_views

urlpatterns = [
    path('stays/', api_views.ipd_stays_api, name='ipd_stays'),
    path('stays/<int:stay_id>/', api_views.ipd_stay_detail_api, name='ipd_stay_detail'),
    path('stays/<int:stay_id>/progress-notes/', api_views.ipd_progress_notes_api, name='ipd_progress_notes'),
    path('stays/<int:stay_id>/rounds/', api_views.ipd_rounds_api, name='ipd_rounds'),
    path('stays/<int:stay_id>/discharge/', api_views.ipd_discharge_api, name='ipd_discharge'),
    path('stays/<int:stay_id>/medication-reconciliation/', api_views.ipd_medication_reconciliation_api, name='ipd_medication_reconciliation'),
    path('stays/<int:stay_id>/mar/', api_views.ipd_mar_api, name='ipd_mar'),
    path('stays/<int:stay_id>/procedures/', api_views.ipd_procedures_api, name='ipd_procedures'),
    path('dashboard/', api_views.ipd_dashboard_api, name='ipd_dashboard'),
]
