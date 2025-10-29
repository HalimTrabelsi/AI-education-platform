from __future__ import annotations

from datetime import datetime

from bson import ObjectId
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from accounts.models import User
from web_project import TemplateLayout

from .forms import MessageForm, StartChatForm
from .models import ChatMessage, ChatRoom, as_object_ids


def _get_user_document(request) -> User:
    return request.user.get_document() if hasattr(request.user, "get_document") else request.user


def _load_user_map(ids: list[str]) -> dict[str, User]:
    object_ids = as_object_ids(ids)
    if not object_ids:
        return {}
    users = User.objects(id__in=object_ids)
    return {str(user.id): user for user in users}


def _ensure_student_teacher_pair(current: User, target: User) -> bool:
    pairs = {("student", "teacher"), ("teacher", "student")}
    return (current.role, target.role) in pairs


@login_required
def chat_list_view(request):
    current_user = _get_user_document(request)
    current_id = str(current_user.id)

    rooms = list(ChatRoom.objects(participant_ids=current_id).order_by("-created_at"))
    partner_ids: list[str] = []
    for room in rooms:
        other = room.other_participant(current_id)
        if other:
            partner_ids.append(other)

    partner_map = _load_user_map(partner_ids + [current_id])

    room_entries = []
    for room in rooms:
        partner_id = room.other_participant(current_id)
        partner = partner_map.get(partner_id) if partner_id else None
        last_message = (
            ChatMessage.objects(room_key=room.room_key).order_by("-created_at").first()
        )
        room_entries.append(
            {
                "room": room,
                "partner": partner,
                "last_message": last_message,
            }
        )

    if current_user.role == "student":
        potential_targets = User.objects(role="teacher", is_blocked=False).order_by("username")
    elif current_user.role == "teacher":
        potential_targets = User.objects(role="student", is_blocked=False).order_by("username")
    else:
        potential_targets = []

    context = TemplateLayout().init(
        {
            "rooms": room_entries,
            "contacts": potential_targets,
            "current_user": current_user,
            "start_chat_form": StartChatForm(),
        }
    )
    context["page_title"] = "Messagerie"
    return render(request, "chat/chat_list.html", context)


@login_required
def start_chat_view(request, user_id: str):
    current_user = _get_user_document(request)
    current_id = str(current_user.id)

    target = User.objects(id=user_id).first()
    if not target:
        messages.error(request, "Utilisateur introuvable.")
        return redirect("chat:list")

    if str(target.id) == current_id:
        messages.error(request, "Vous ne pouvez pas discuter avec vous-même.")
        return redirect("chat:list")

    if getattr(target, "is_blocked", False):
        messages.error(request, "Ce compte est actuellement bloqué.")
        return redirect("chat:list")

    if not _ensure_student_teacher_pair(current_user, target):
        messages.error(request, "La messagerie n'est disponible qu'entre étudiants et enseignants.")
        return redirect("chat:list")

    room = ChatRoom.get_or_create(current_id, str(target.id))
    return redirect("chat:room", room_key=room.room_key)


@login_required
def chat_room_view(request, room_key: str):
    current_user = _get_user_document(request)
    current_id = str(current_user.id)

    room = ChatRoom.objects(room_key=room_key).first()
    if not room or not room.contains(current_id):
        messages.error(request, "Salon introuvable.")
        return redirect("chat:list")

    partner_map = _load_user_map(room.participant_ids)
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            ChatMessage(
                room_key=room.room_key,
                sender_id=current_id,
                content=form.cleaned_data["message"],
                created_at=datetime.utcnow(),
            ).save()
            messages.success(request, "Message envoyé.")
            return redirect("chat:room", room_key=room.room_key)
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = MessageForm()

    messages_qs = ChatMessage.fetch_for_room(room.room_key)
    rendered_messages = [
        {
            "object": msg,
            "sender": partner_map.get(str(msg.sender_id)),
            "is_self": str(msg.sender_id) == current_id,
        }
        for msg in messages_qs
    ]
    context = TemplateLayout().init(
        {
            "room": room,
            "messages": rendered_messages,
            "participant_map": partner_map,
            "current_user": current_user,
            "form": form,
        }
    )
    context["page_title"] = "Discussion"
    return render(request, "chat/chat_room.html", context)
