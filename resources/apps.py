from django.apps import AppConfig


class ResourcesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'resources'

    def ready(self):
        try:
            import resources.signals
        except Exception:
            # Optional dependencies may be missing in dev environments
            pass
