from django import forms


class ObjectiveForm(forms.Form):
    titre = forms.CharField(max_length=255, required=True, label="Titre")
    description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        label="Description",
    )
    filiere = forms.CharField(max_length=100, required=True, label="Filière")
    niveau = forms.CharField(max_length=50, required=True, label="Niveau")
    priorite = forms.ChoiceField(
        choices=[
            ("haute", "Haute"),
            ("moyenne", "Moyenne"),
            ("basse", "Basse"),
        ],
        label="Priorité",
    )
    etat = forms.ChoiceField(
        choices=[
            ("non commencé", "Non commencé"),
            ("en cours", "En cours"),
            ("terminé", "Terminé"),
        ],
        label="État",
    )
    date_debut = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Date de début",
    )
    date_echeance = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Date d’échéance",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            base_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.setdefault("class", base_class)
