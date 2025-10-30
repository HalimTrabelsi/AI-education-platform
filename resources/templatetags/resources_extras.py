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
def is_pdf(value):
    """Vérifie si le fichier est un PDF"""
    if not value:
        return False
    return str(value).lower().endswith('.pdf')

@register.filter
def split(value, key):
    """Sépare une chaîne ou retourne la liste telle quelle"""
    if not value:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(key) if v.strip()]
    elif isinstance(value, (list, tuple)):
        return value
    return []
@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key)
    except AttributeError:
        return None

