from datetime import datetime
from typing import List

from mongoengine import (
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)

from resources.models import Resource


class QuizQuestion(EmbeddedDocument):
    prompt = StringField(required=True)
    options = ListField(StringField(), required=True)
    answer_index = IntField(required=True)


class Quiz(Document):
    meta = {"collection": "quizzes"}

    resource = ReferenceField(Resource, required=True)
    title = StringField(required=True)
    questions = ListField(EmbeddedDocumentField(QuizQuestion))
    created_at = DateTimeField(default=datetime.utcnow)

    def question_count(self) -> int:
        return len(self.questions or [])


class QuizAttempt(Document):
    meta = {"collection": "quiz_attempts"}

    quiz = ReferenceField(Quiz, required=True)
    user_id = StringField(required=True)
    score = IntField(required=True)
    total_questions = IntField(required=True)
    answers = ListField(IntField())
    created_at = DateTimeField(default=datetime.utcnow)

    @property
    def percentage(self) -> float:
        if not self.total_questions:
            return 0.0
        return round((self.score / self.total_questions) * 100, 2)
