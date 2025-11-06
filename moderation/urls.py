from django.urls import path
from . import views

app_name = "moderation"

urlpatterns = [
    path("", views.report_list, name="report_list"),
    path("create/", views.report_create, name="report_create"),
    path("update/<str:report_id>/", views.report_update, name="report_update"),
    path("delete/<str:report_id>/", views.report_delete, name="report_delete"),
    path("data/", views.report_data, name="report_data"),
    path("verify-ai/", views.verify_ai, name="verify_ai"),
    path("export/pdf/", views.export_reports_pdf, name="export_pdf"),
    path("report_stats/", views.report_stats, name="report_stats"),


]
