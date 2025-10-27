from django import forms
from .models import FeedItem


class FeedItemForm(forms.ModelForm):

    class Meta:
        model = FeedItem
        fields = ['title', 'description', 'content_type', 'deadline', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Entrez le titre du contenu'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Décrivez le contenu en détail...'
            }),
            'content_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': 'Titre',
            'description': 'Description',
            'content_type': 'Type de contenu',
            'deadline': 'Date limite (optionnel)',
            'is_active': 'Actif dans le feed'
        }
        help_texts = {
            'deadline': 'Pour les échéances uniquement',
        }
    
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
    