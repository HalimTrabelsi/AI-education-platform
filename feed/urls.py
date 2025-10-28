from django.urls import path
from . import views

app_name = 'feed'

urlpatterns = [

    path('', views.feed_list, name='list'),
    path('create/', views.feed_create, name='create'),
    
    path('export/pdf/', views.feed_export_pdf, name='export_pdf'),
    
    path('ai/check-content/', views.ai_check_content, name='ai_check_content'),
    path('ai/weekly-summary/', views.generate_weekly_summary, name='generate_weekly_summary'),
    path('ai/missing-content/', views.check_missing_content, name='check_missing_content'),
    path('ai/deadline-reminders/', views.generate_deadline_reminders, name='generate_deadline_reminders'),
    path('ai/analyze-content/', views.ai_analyze_content, name='ai_analyze_content'),
    path('ai/suggest-title/', views.ai_suggest_title, name='ai_suggest_title'),
    path('ai/dashboard/', views.ai_dashboard, name='ai_dashboard'),
    
    path('<str:pk>/', views.feed_detail, name='detail'),
    path('<str:pk>/update/', views.feed_update, name='update'),
    path('<str:pk>/delete/', views.feed_delete, name='delete'),
]
