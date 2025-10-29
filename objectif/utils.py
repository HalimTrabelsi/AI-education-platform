from mongoengine import DoesNotExist
from accounts.models import User

def _get_mongo_user(request_user):
    """
    Utilitaire pour récupérer le vrai utilisateur MongoDB
    depuis request.user (peut être un adaptateur ou un User direct)
    """
    try:
        if hasattr(request_user, 'get_document'):
            # Si c'est un adaptateur Django
            return request_user.get_document()
        elif hasattr(request_user, '_mongo_user'):
            # Si c'est un adaptateur avec _mongo_user
            return request_user._mongo_user
        else:
            # Si c'est déjà un User MongoDB direct
            return request_user
    except Exception:
        # En cas d'erreur, essayer de récupérer l'user par l'ID de session
        return request_user