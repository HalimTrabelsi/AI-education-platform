from django import forms

from .models import RESOURCE_TYPES, validate_file


class ResourceForm(forms.Form):
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea, required=False)
    file = forms.FileField(validators=[validate_file])
    resource_type = forms.ChoiceField(choices=[(choice, choice) for choice in RESOURCE_TYPES])
    tags = forms.CharField(required=False, help_text="Separer les tags par des virgules")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["description"].widget.attrs.update(
            {"class": "form-control", "rows": 4}
        )
        self.fields["file"].widget.attrs.update({"class": "form-control"})
        self.fields["resource_type"].widget.attrs.update({"class": "form-select"})
        self.fields["tags"].widget.attrs.update({"class": "form-control"})
