from django import forms

from .utils import mask_bad_words


class StartChatForm(forms.Form):
    target_user_id = forms.CharField(required=True, widget=forms.HiddenInput())


class MessageForm(forms.Form):
    message = forms.CharField(
        label="Message",
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Écrivez votre message…",
                "class": "form-control",
            }
        ),
    )

    def clean_message(self):
        text = self.cleaned_data["message"].strip()
        if not text:
            raise forms.ValidationError("Le message ne peut pas être vide.")
        return mask_bad_words(text)
