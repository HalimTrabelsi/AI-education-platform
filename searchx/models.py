from django.db import models
from django.conf import settings

class Concept(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Collection(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    filiere = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=10, blank=True)
    concepts = models.ManyToManyField(Concept, related_name="collections", blank=True)
    resources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class UserInteraction(models.Model):
    EVENT_CHOICES = (
        ("search", "search"),
        ("view", "view"),
        ("upload", "upload"),
        ("click", "click"),
    )
    user = models.ForeignKey(getattr(settings, 'AUTH_USER_MODEL', 'auth.User'), null=True, blank=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    query = models.TextField(blank=True)
    content_type = models.CharField(max_length=50, blank=True)
    content_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user_id or 'anon'}:{self.event_type}:{self.created_at:%Y-%m-%d %H:%M}"
