from django.urls import path
from . import views

app_name = "objectif"

urlpatterns = [
    path('', views.list_objectif, name='list'),
    path('create/', views.create_objectif, name='create'),
    path('<str:id>/update/', views.update_objectif, name='update'),
    path('<str:id>/delete/', views.delete_objectif, name='delete'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('chatbot/api/', views.chatbot_api, name='chatbot_api'),  # Garder chatbot_api pour l'API

    # Détails et QR Code
    path('details/<str:obj_id>/', views.objective_details, name='objective_details'),
    path('qrcode/<str:obj_id>/', views.generate_qrcode, name='generate_qrcode'),
    path('api/<str:obj_id>/', views.objective_json, name='objective_json'),
    
    # Calendrier
    path('calendar/', views.objective_calendar, name='calendar'),
    path('calendar/api/', views.calendar_events_api, name='calendar_events_api'),
     path('details/<str:obj_id>/', views.objective_details, name='details'),
    path('details/<str:obj_id>/ia-analysis/', views.trigger_ia_analysis, name='trigger_ia_analysis'),
    path('api/<str:obj_id>/ia-analysis/', views.get_ia_analysis, name='get_ia_analysis'),
    path('assistant/', views.chatbot_view, name='assistant'),


    path('bilan-pdf/<str:obj_id>/', views.generate_pdf_bilan, name='generate_pdf_bilan'),


]
