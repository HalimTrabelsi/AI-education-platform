from django import template

register = template.Library()

@register.filter
def split(value, sep=','):
    try:
        return [s.strip() for s in (value or '').split(sep) if s.strip()]
    except Exception:
        return []

@register.filter
def is_video(filename):
    try:
        name = (filename or '').lower()
        return any(name.endswith(ext) for ext in ['.mp4', '.mov', '.avi', '.webm', '.mkv'])
    except Exception:
        return False
