from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('users/<str:user_id>/toggle-block/', views.toggle_user_block, name='toggle-user-block'),
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
]
