from django import forms

class ObjectiveForm(forms.Form):
    titre = forms.CharField(max_length=255, required=True)
    description = forms.CharField(widget=forms.Textarea, required=False)
    filiere = forms.CharField(max_length=100, required=True)
    niveau = forms.CharField(max_length=50, required=True)
    priorite = forms.ChoiceField(choices=[('haute','Haute'),('moyenne','Moyenne'),('basse','Basse')])
    etat = forms.ChoiceField(choices=[('non commencé','Non commencé'),('en cours','En cours'),('terminé','Terminé')])
    date_debut = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type':'datetime-local'}))
    date_echeance = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type':'datetime-local'}))
