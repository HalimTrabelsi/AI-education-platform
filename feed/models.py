from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class FeedItem(models.Model):
 
    CONTENT_TYPE_CHOICES = [
        ('programme', 'Programme'),
        ('echeance', 'Échéance'),
        ('difficulte', 'Difficulté'),
        ('ressource', 'Ressource'),
        ('annonce', 'Annonce'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    description = models.TextField(
        verbose_name="Description"
    )
    
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='programme',
        verbose_name="Type de contenu"
    )
    
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feed_items',
        verbose_name="Auteur"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date limite",
        help_text="Pour les échéances uniquement"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    class Meta:
        verbose_name = "Élément du Feed"
        verbose_name_plural = "Éléments du Feed"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def is_urgent(self):
 
        if self.deadline:
            delta = self.deadline - timezone.now()
            return delta.days <= 3
        return False
    
    