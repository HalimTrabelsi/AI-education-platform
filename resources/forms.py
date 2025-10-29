from django import forms
from .models import RESOURCE_TYPES, validate_file

class ResourceForm(forms.Form):
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea, required=False)
    file = forms.FileField(validators=[validate_file])
    resource_type = forms.ChoiceField(choices=[(x, x) for x in RESOURCE_TYPES])
    tags = forms.CharField(required=False, help_text="Séparer les tags par des virgules")
