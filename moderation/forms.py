from django import forms

class ReportForm(forms.Form):
    title = forms.CharField(max_length=100, label="Titre")
    description = forms.CharField(widget=forms.Textarea, required=False, label="Description")
    resource_url = forms.URLField(required=False, label="URL de la ressource")
    flagged_by = forms.CharField(max_length=50, label="Signalé par")
    is_plagiarism = forms.BooleanField(required=False, label="Plagiat (manuel)")
    is_nsfw = forms.BooleanField(required=False, label="NSFW (manuel)")
    ai_confidence = forms.FloatField(required=False, label="Score IA (optionnel)")
