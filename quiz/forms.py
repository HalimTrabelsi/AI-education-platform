from django import forms


class QuizAnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop("questions")
        super().__init__(*args, **kwargs)
        for index, question in enumerate(questions):
            field_name = f"question_{index}"
            self.fields[field_name] = forms.ChoiceField(
                label=question.prompt,
                choices=[(i, option) for i, option in enumerate(question.options)],
                widget=forms.RadioSelect,
                required=True,
            )
