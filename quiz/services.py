import random
from typing import List

from resources.models import Resource
from .models import Quiz, QuizQuestion


FALLBACK_OPTIONS = [
    "Je ne sais pas",
    "Toutes les réponses",
    "Aucune idée",
    "Peut-être",
]


def _pick_keywords(text: str, count: int = 3) -> List[str]:
    words = [w for w in text.split() if len(w) > 4]
    if not words:
        return []
    random.shuffle(words)
    seen = []
    for word in words:
        cleaned = word.strip(",.;:!?\"'()[]{}")
        if cleaned.lower() not in {w.lower() for w in seen}:
            seen.append(cleaned)
        if len(seen) >= count:
            break
    return seen


def _build_question_from_sentence(sentence: str) -> QuizQuestion:
    keywords = _pick_keywords(sentence, count=1)
    if not keywords:
        blank_sentence = sentence
        answer = ""
    else:
        answer = keywords[0]
        blank_sentence = sentence.replace(answer, "____", 1)

    distractors = [w for w in _pick_keywords(sentence, count=4) if w != answer][:3]
    while len(distractors) < 3:
        distractors.append(random.choice(FALLBACK_OPTIONS))

    options = distractors + [answer or sentence]
    random.shuffle(options)
    answer_index = options.index(answer or sentence)
    return QuizQuestion(prompt=blank_sentence.strip(), options=options, answer_index=answer_index)


def generate_quiz_for_resource(resource: Resource, force: bool = False) -> Quiz:
    existing = Quiz.objects(resource=resource).first()
    if existing and not force:
        return existing

    base_text = resource.content_text or resource.description or ""
    sentences = [s.strip() for s in base_text.split(".") if len(s.strip()) > 20]
    if not sentences:
        sentences = [f"Ce cours traite de {resource.title}."]

    questions = []
    for sentence in sentences[:5]:
        questions.append(_build_question_from_sentence(sentence))

    quiz = existing or Quiz(resource=resource)
    quiz.title = f"Quiz - {resource.title}"
    quiz.questions = questions
    quiz.save()
    return quiz
