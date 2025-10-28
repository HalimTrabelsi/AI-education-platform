from django import forms
from .models import FeedItem


class FeedItemForm(forms.Form):
    """
    Formulaire pour créer/modifier un FeedItem MongoDB
    """
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez le titre du contenu'
        }),
        label='Titre'
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Décrivez le contenu en détail...'
        }),
        label='Description'
    )
    
    content_type = forms.ChoiceField(
        choices=FeedItem.CONTENT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Type de contenu',
        initial='programme'
    )
    
    deadline = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Date limite (optionnel)',
        help_text='Pour les échéances uniquement'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Actif dans le feed'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        deadline = cleaned_data.get('deadline')
        
        if content_type == 'echeance' and not deadline:
            raise forms.ValidationError(
                "Une date limite est obligatoire pour les échéances."
            )
        
        return cleaned_data


class FeedItemSearchForm(forms.Form):
    """
    Formulaire de recherche pour les FeedItems
    """
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher dans le feed...'
        }),
        label='Recherche'
    )
    
    content_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les types')] + FeedItem.CONTENT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Type de contenu'
    )
    
    ordering = forms.ChoiceField(
        required=False,
        choices=[
            ('-created_at', 'Plus récent'),
            ('created_at', 'Plus ancien'),
            ('title', 'Titre A-Z'),
            ('-title', 'Titre Z-A'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Trier par',
        initial='-created_at'
    )