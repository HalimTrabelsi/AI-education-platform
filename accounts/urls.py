from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('admin/users/bulk-action/', views.admin_bulk_user_action, name='admin-bulk-action'),
    path('admin/users/<str:user_id>/impersonate/', views.admin_impersonate_user, name='admin-impersonate'),
    path('admin/stop-impersonation/', views.admin_stop_impersonation, name='admin-stop-impersonation'),
    path('users/<str:user_id>/toggle-block/', views.toggle_user_block, name='toggle-user-block'),
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
]
