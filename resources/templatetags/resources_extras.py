from django import template

register = template.Library()

@register.filter
def is_image(value):
    """Vérifie si le fichier est une image"""
    if not value:
        return False
    return str(value).lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))

@register.filter
def is_video(value):
    """Vérifie si le fichier est une vidéo"""
    if not value:
        return False
    return str(value).lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))

@register.filter
def split(value, key):
    """Sépare une chaîne en fonction du séparateur donné"""
    if not value:
        return []
    return [v.strip() for v in value.split(key)]
