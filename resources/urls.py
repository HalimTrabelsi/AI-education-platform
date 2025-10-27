from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.conf import settings
from .views import (
    ResourceViewSet,
    resource_list,
    ResourceUpdateView,
    ResourceDeleteView,
    front_office_resource_list,
    resource_detail,
    front_office_resource_add,
    resource_edit
)

router = DefaultRouter()
router.register(r'resources', ResourceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('list/', resource_list, name='resource-list'),  
    path('resources/<int:pk>/edit/', resource_edit, name='resource-update'),    
    path('<int:pk>/delete/', ResourceDeleteView.as_view(), name='resource-delete'),
    path('front/', front_office_resource_list, name='front_office_resource_list'),
    path('<int:pk>/', resource_detail, name='resource_detail'),
    path('front/add/', front_office_resource_add, name='front_office_resource_add'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
