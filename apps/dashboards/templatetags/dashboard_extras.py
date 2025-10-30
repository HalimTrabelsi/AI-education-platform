from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely return dictionary[key] if it exists."""
    try:
        return dictionary.get(key)
    except AttributeError:
        return None
