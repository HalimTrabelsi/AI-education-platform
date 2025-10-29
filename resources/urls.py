from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.conf import settings
from .views import (
    ResourceViewSet,
    resource_list,
    front_office_resource_list,
    resource_detail,
    front_office_resource_add,
    resource_edit,
    resource_delete,
    generate_summary_view,
)

# --- Déclaration du router DRF ---
router = DefaultRouter()
router.register(r'resources', ResourceViewSet, basename='resource')

urlpatterns = [

    # --- Back-office ---
    path('list/', resource_list, name='resource-list'),
    path('resources/<str:pk>/edit/', resource_edit, name='resource-update'),
    path('resources/<str:pk>/delete/', resource_delete, name='resource-delete'),

    # --- Front-office ---
    path('front/', front_office_resource_list, name='front_office_resource_list'),
    path('front/resource/<str:pk>/', resource_detail, name='front_office_resource_detail'),
    path('front/add/', front_office_resource_add, name='front_office_resource_add'),


    path('api/<str:resource_id>/generate-summary/', generate_summary_view, name='generate_summary'),

]

# --- Fichiers statiques & médias en debug ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
