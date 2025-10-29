from datetime import datetime
from typing import Iterable, Sequence

from bson import ObjectId
from mongoengine import (
    DateTimeField,
    Document,
    ListField,
    StringField,
)


class ChatRoom(Document):
    meta = {
        "collection": "chat_rooms",
        "indexes": [
            {"fields": ["room_key"], "unique": True},
            {"fields": ["participant_ids"]},
        ],
    }

    room_key = StringField(required=True, unique=True)
    participant_ids = ListField(StringField(required=True), required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    @classmethod
    def build_room_key(cls, user_ids: Sequence[str]) -> str:
        return ":".join(sorted({str(_id) for _id in user_ids}))

    @classmethod
    def get_or_create(cls, user_id: str, target_id: str) -> "ChatRoom":
        key = cls.build_room_key([user_id, target_id])
        room = cls.objects(room_key=key).first()
        if room:
            return room
        room = cls(
            room_key=key,
            participant_ids=sorted([str(user_id), str(target_id)]),
        )
        room.save()
        return room

    def other_participant(self, current_id: str) -> str | None:
        for participant in self.participant_ids:
            if participant != str(current_id):
                return participant
        return None

    def contains(self, user_id: str) -> bool:
        return str(user_id) in self.participant_ids


class ChatMessage(Document):
    meta = {
        "collection": "chat_messages",
        "indexes": [
            "room_key",
            "-created_at",
        ],
        "ordering": ["created_at"],
    }

    room_key = StringField(required=True)
    sender_id = StringField(required=True)
    content = StringField(required=True, max_length=2000)
    created_at = DateTimeField(default=datetime.utcnow)

    @classmethod
    def fetch_for_room(cls, room_key: str) -> Iterable["ChatMessage"]:
        return cls.objects(room_key=room_key).order_by("created_at")

    @classmethod
    def delete_room(cls, room_key: str) -> None:
        cls.objects(room_key=room_key).delete()


def as_object_ids(id_list: Iterable[str]) -> list[ObjectId]:
    """Utility to convert string ids to ObjectId safely."""
    result = []
    for value in id_list:
        try:
            result.append(ObjectId(str(value)))
        except Exception:
            continue
    return result
