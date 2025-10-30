from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from accounts.decorators import role_required
from resources.models import Resource
from web_project import TemplateLayout

from .forms import QuizAnswerForm
from .models import Quiz, QuizAttempt
from .services import generate_quiz_for_resource


def _layout_context(data=None):
    return TemplateLayout().init(data or {})


@role_required("student", "teacher", "admin")
def quiz_list_view(request):
    user_id = str(getattr(request.user, "pk", ""))
    quizzes = Quiz.objects.order_by("-created_at")
    attempts = {attempt.quiz.id: attempt for attempt in QuizAttempt.objects(user_id=user_id)}

    context = _layout_context({
        "quizzes": quizzes,
        "attempts": attempts,
    })
    return render(request, "quiz/quiz_list.html", context)


@role_required("student", "teacher", "admin")
def quiz_take_view(request, resource_id):
    resource = Resource.objects(id=resource_id).first()
    if not resource:
        messages.error(request, "Resource not found.")
        return redirect("quiz:list")

    quiz = generate_quiz_for_resource(resource)
    form = QuizAnswerForm(request.POST or None, questions=quiz.questions)

    if request.method == "POST" and form.is_valid():
        answers = []
        score = 0
        for index, question in enumerate(quiz.questions):
            field = f"question_{index}"
            selected = int(form.cleaned_data[field])
            answers.append(selected)
            if selected == question.answer_index:
                score += 1

        attempt = QuizAttempt(
            quiz=quiz,
            user_id=str(getattr(request.user, "pk", "")),
            score=score,
            total_questions=quiz.question_count(),
            answers=answers,
        )
        attempt.save()
        messages.success(request, "Quiz submitted. Check your score!")
        return redirect(reverse("quiz:result", args=[attempt.id]))

    context = _layout_context({
        "quiz": quiz,
        "resource": resource,
        "form": form,
    })
    return render(request, "quiz/quiz_take.html", context)


@role_required("student", "teacher", "admin")
def quiz_result_view(request, attempt_id):
    attempt = QuizAttempt.objects(id=attempt_id).first()
    if not attempt:
        messages.error(request, "Result not found.")
        return redirect("quiz:list")

    quiz = attempt.quiz
    context = _layout_context({
        "attempt": attempt,
        "quiz": quiz,
    })
    return render(request, "quiz/quiz_result.html", context)
