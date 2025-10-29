from mongoengine import Document, StringField, DateTimeField, BooleanField, ListField, FloatField, DictField
from datetime import datetime, timedelta
from django.utils import timezone


class FeedItem(Document):
    """
    Modèle MongoDB pour les éléments du feed
    """
    CONTENT_TYPE_CHOICES = [
        ('programme', 'Programme'),
        ('echeance', 'Échéance'),
        ('difficulte', 'Difficulté'),
        ('ressource', 'Ressource'),
        ('annonce', 'Annonce'),
    ]
    
    title = StringField(max_length=200, required=True, verbose_name="Titre")
    description = StringField(required=True, verbose_name="Description")
    content_type = StringField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='programme',
        verbose_name="Type de contenu"
    )
    author_id = StringField(max_length=24, required=True, verbose_name="ID Auteur")
    created_at = DateTimeField(default=datetime.utcnow, verbose_name="Date de création")
    updated_at = DateTimeField(default=datetime.utcnow, verbose_name="Dernière mise à jour")
    deadline = DateTimeField(null=True, verbose_name="Date limite")
    is_active = BooleanField(default=True, verbose_name="Actif")
    
    ai_suggestions = ListField(StringField(), verbose_name="Suggestions IA")
    ai_extracted_dates = ListField(StringField(), verbose_name="Dates extraites")
    ai_quality_score = FloatField(default=0.0, verbose_name="Score qualité IA")
    ai_tone = StringField(max_length=50, verbose_name="Ton détecté")
    suggested_resources = ListField(StringField(), verbose_name="Ressources suggérées")
    is_ai_generated = BooleanField(default=False, verbose_name="Généré par IA")

    tiktok_video_url = StringField(null=True, verbose_name="URL Vidéo TikTok")
    tiktok_video_status = StringField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('processing', 'En cours'),
            ('completed', 'Terminé'),
            ('failed', 'Échec')
        ],
        default='pending',
        verbose_name="Statut Vidéo"
    )
    tiktok_generation_date = DateTimeField(null=True, verbose_name="Date génération vidéo")
    tiktok_metadata = DictField(verbose_name="Métadonnées vidéo")
    
    meta = {
        'collection': 'feed_feeditem',
        'ordering': ['-created_at'],
        'indexes': ['author_id', 'content_type', 'is_active', '-created_at']
    }
    
    def __str__(self):
        return self.title
    
    @property
    def author(self):
        """Récupère l'objet User depuis MongoDB"""
        try:
            from accounts.models import User
            return User.objects.get(id=self.author_id)
        except Exception:
            return None
    
    def get_author_username(self):
        """Retourne le nom d'utilisateur ou 'Utilisateur inconnu'"""
        user = self.author
        return user.username if user else "Utilisateur inconnu"
    
    def is_urgent(self):
        """Vérifie si l'échéance est urgente (moins de 3 jours)"""
        if self.deadline:
            now = timezone.now()
            if timezone.is_naive(self.deadline):
                deadline_aware = timezone.make_aware(self.deadline)
            else:
                deadline_aware = self.deadline
            
            delta = deadline_aware - now
            return delta.days <= 3
        return False
    
    def save(self, *args, **kwargs):
        """Met à jour la date de modification"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)