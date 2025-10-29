from django.urls import path

from . import views

app_name = "objectifs"

urlpatterns = [
    path("", views.list_objectif, name="list"),
    path("create/", views.create_objectif, name="create"),
    path("<str:obj_id>/update/", views.update_objectif, name="update"),
    path("<str:obj_id>/delete/", views.delete_objectif, name="delete"),

    # Assistant IA
    path("assistant/", views.chatbot_view, name="assistant"),
    path("assistant/api/", views.chatbot_api, name="assistant_api"),

    # Détails & exports
    path("<str:obj_id>/", views.objective_details, name="detail"),
    path("<str:obj_id>/qr/", views.generate_qrcode, name="qrcode"),
    path("<str:obj_id>/json/", views.objective_json, name="json"),
    path("<str:obj_id>/bilan-pdf/", views.generate_pdf_bilan, name="bilan_pdf"),
    path("<str:obj_id>/ia-analysis/", views.trigger_ia_analysis, name="ia_analysis"),
    path("api/<str:obj_id>/ia-analysis/", views.get_ia_analysis, name="ia_analysis_data"),

    # Calendrier
    path("calendar/", views.objective_calendar, name="calendar"),
    path("calendar/api/", views.calendar_events_api, name="calendar_api"),
]
