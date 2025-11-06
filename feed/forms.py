from django import forms
from .models import FeedItem
from .ai_services import AIWritingAssistant, AIContentEnricher


class FeedItemForm(forms.Form):
    """
    Formulaire pour créer/modifier un FeedItem MongoDB avec assistance IA
    """
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez le titre du contenu',
            'id': 'id_title'
        }),
        label='Titre'
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Décrivez le contenu en détail...',
            'id': 'id_description'
        }),
        label='Description'
    )
    
    content_type = forms.ChoiceField(
        choices=FeedItem.CONTENT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_content_type'
        }),
        label='Type de contenu',
        initial='programme'
    )
    
    deadline = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'id': 'id_deadline'
        }),
        label='Date limite (optionnel)',
        help_text='Pour les échéances uniquement',
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_is_active'
        }),
        label='Actif dans le feed'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_assistant = AIWritingAssistant()
        self.ai_enricher = AIContentEnricher()
        self.ai_suggestions = []
        self.grammar_suggestions = []
    
    def clean_description(self):
        """
        Validation avec suggestions IA
        """
        description = self.cleaned_data.get('description')
        
        if not description:
            return description
        
        # Stocker les suggestions pour les afficher plus tard
        content_type = self.data.get('content_type', 'programme')
        self.ai_suggestions = self.ai_assistant.suggest_improvements(
            description,
            content_type
        )
        
        # Vérifier grammaire
        self.grammar_suggestions = self.ai_assistant.check_grammar(description)
        
        return description
    
    def clean(self):
        """
        Validation globale avec enrichissement IA
        """
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        deadline = cleaned_data.get('deadline')
        description = cleaned_data.get('description')
        
        # Vérifier échéance obligatoire pour type "echéance"
        if content_type == 'echeance' and not deadline:
            raise forms.ValidationError(
                "Une date limite est obligatoire pour les échéances."
            )
        
        # Extraire dates automatiquement
        if description and content_type:
            extracted_dates = self.ai_enricher.extract_dates(description)
            
            # Si aucune deadline n'est définie mais qu'une date est détectée
            if not deadline and extracted_dates and content_type == 'echeance':
                # Suggérer la première date valide
                for date_info in extracted_dates:
                    if date_info['parsed_date']:
                        self.add_error(
                            'deadline',
                            f"💡 Date détectée dans le texte: '{date_info['text']}'. Voulez-vous l'utiliser comme deadline ?"
                        )
                        break
        
        return cleaned_data
    
    def save(self, author_id):
        """
        Sauvegarde avec enrichissement IA complet
        """
        feed_item = FeedItem(
            title=self.cleaned_data['title'],
            description=self.cleaned_data['description'],
            content_type=self.cleaned_data['content_type'],
            author_id=author_id,
            deadline=self.cleaned_data.get('deadline'),
            is_active=self.cleaned_data.get('is_active', True)
        )
        
        # === ENRICHISSEMENT IA ===
        
        # 1. Stocker les suggestions d'amélioration
        feed_item.ai_suggestions = self.ai_suggestions
        
        # 2. Extraire et stocker les dates
        extracted_dates = self.ai_enricher.extract_dates(feed_item.description)
        feed_item.ai_extracted_dates = [d['text'] for d in extracted_dates]
        
        # 3. Suggérer ressources
        feed_item.suggested_resources = self.ai_enricher.suggest_resources(
            feed_item.description,
            feed_item.content_type
        )
        
        # 4. Adapter le ton si nécessaire
        adapted_description = self.ai_assistant.adapt_tone(
            feed_item.description,
            feed_item.content_type
        )
        if adapted_description != feed_item.description:
            feed_item.description = adapted_description
        
        # 5. Déterminer le ton
        description_lower = feed_item.description.lower()
        if 'urgent' in description_lower or 'immédiat' in description_lower:
            feed_item.ai_tone = 'urgent'
        elif any(word in description_lower for word in ['merci', 'cordialement', 'veuillez']):
            feed_item.ai_tone = 'formel'
        else:
            feed_item.ai_tone = 'informatif'
        
        # 6. Calculer score qualité
        quality_score = 5.0
        
        # Bonus pour longueur appropriée
        if len(feed_item.description) > 100:
            quality_score += 2.0
        
        # Bonus pour deadline définie
        if feed_item.deadline:
            quality_score += 1.0
        
        # Bonus pour peu d'erreurs grammaticales
        if len(self.grammar_suggestions) == 0:
            quality_score += 2.0
        elif len(self.grammar_suggestions) <= 2:
            quality_score += 1.0
        
        # Pénalité pour erreurs graves
        if len(self.grammar_suggestions) > 5:
            quality_score -= 1.0
        
        feed_item.ai_quality_score = min(max(quality_score, 0.0), 10.0)
        
        # Sauvegarder
        feed_item.save()
        return feed_item


class FeedItemSearchForm(forms.Form):
    """
    Formulaire de recherche pour les FeedItems
    """
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher dans le feed...',
            'id': 'id_search_query'
        }),
        label='Recherche'
    )
    
    content_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les types')] + FeedItem.CONTENT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_filter_content_type'
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
            'class': 'form-select',
            'id': 'id_ordering'
        }),
        label='Trier par',
        initial='-created_at'
    )