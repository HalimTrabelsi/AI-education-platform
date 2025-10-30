from django import forms
from .models import Concept, Collection
import json


class ConceptForm(forms.ModelForm):
    class Meta:
        model = Concept
        fields = ["name", "description", "level"]


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["name", "description", "filiere", "level", "concepts", "resources"]
        widgets = {
            "concepts": forms.CheckboxSelectMultiple(),
            "resources": forms.Textarea(attrs={"rows": 4, "placeholder": "JSON list, e.g. [{\"type\":\"pdf\",\"title\":\"Doc\"}]"}),
        }

    def clean_resources(self):
        data = self.cleaned_data.get("resources")
        # Accept empty as []
        if data in (None, ""):
            return []
        # If already a list/dict, return as-is
        if isinstance(data, (list, dict)):
            return data
        # Try to parse JSON from string
        try:
            parsed = json.loads(data)
        except Exception:
            raise forms.ValidationError("Resources must be valid JSON (list or object)")
        # Normalize to list
        if parsed is None:
            return []
        return parsed
