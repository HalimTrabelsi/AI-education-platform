from django.urls import path
from . import views

app_name = "moderation"

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('data/', views.report_data, name='report_data'),
    path('stats/', views.report_stats, name='report_stats'),
    path('report/new/', views.report_create, name='report_create'),
    path('report/<str:report_id>/edit/', views.report_update, name='report_update'),
    path('report/<str:report_id>/delete/', views.report_delete, name='report_delete'),
    path('export/pdf/', views.export_reports_pdf, name='export_reports_pdf'),  # PDF export
]
