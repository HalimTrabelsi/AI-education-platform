from django.urls import path, include

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    # ex: path('', dashboard_view, name='dashboard'),
]
