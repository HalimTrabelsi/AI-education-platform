from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from . import views

app_name = "resources"

router = None
try:
    from rest_framework.routers import DefaultRouter

    if views.viewsets:
        router = DefaultRouter()
        router.register(r"resources", views.ResourceViewSet, basename="resource")
except Exception:
    router = None

urlpatterns = [
    # Back-office routes
    path("back-office/", views.resource_list, name="list"),
    path("back-office/add/", views.resource_add, name="add"),
    path("back-office/<str:pk>/edit/", views.resource_edit, name="edit"),
    path("back-office/<str:pk>/delete/", views.resource_delete, name="delete"),

    # Front-office routes
    path("front-office/", views.front_office_resource_list, name="front"),
    path("front-office/<str:pk>/", views.resource_detail, name="detail"),

    path(
        "api/<str:resource_id>/generate-summary/",
        views.generate_summary_view,
        name="generate_summary",
    ),
]

if router:
    urlpatterns += [path("api/", include(router.urls))]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
