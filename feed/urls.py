from django.urls import path
from . import views

app_name = 'feed'

urlpatterns = [
    # Liste
    path('', views.feed_list, name='list'),
    
    # Création
    path('create/', views.feed_create, name='create'),
    
    # Détail
    path('<int:pk>/', views.feed_detail, name='detail'),
    
    # Modification
    path('<int:pk>/update/', views.feed_update, name='update'),
    
    # Suppression
    path('<int:pk>/delete/', views.feed_delete, name='delete'),
]
