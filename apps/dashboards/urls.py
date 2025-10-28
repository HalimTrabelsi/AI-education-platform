from django.urls import path

from .views import DashboardsView

app_name = "dashboards"

urlpatterns = [
    path(
        "",
        DashboardsView.as_view(template_name="dashboard_analytics.html"),
        name="home",
    )
]
