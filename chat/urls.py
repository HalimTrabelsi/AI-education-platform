from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_list_view, name="list"),
    path("start/<str:user_id>/", views.start_chat_view, name="start"),
    path("room/<str:room_key>/", views.chat_room_view, name="room"),
]
