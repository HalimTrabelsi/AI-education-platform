from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.quiz_list_view, name="list"),
    path("resource/<str:resource_id>/", views.quiz_take_view, name="take"),
    path("attempt/<str:attempt_id>/", views.quiz_result_view, name="result"),
]
