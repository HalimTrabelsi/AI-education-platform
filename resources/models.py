from mongoengine import Document, StringField, ListField, DateTimeField, BooleanField, DictField
import datetime
from pdf2image import convert_from_path
from io import BytesIO
import os
from django.core.exceptions import ValidationError

RESOURCE_TYPES = ['PDF', 'VIDEO', 'IMAGE']

class Resource(Document):
    title = StringField(max_length=255, required=True)
    description = StringField()
    file = StringField()  # chemin ou URL du fichier
    resource_type = StringField(choices=RESOURCE_TYPES)
    tags = ListField(StringField())
    uploaded_at = DateTimeField(default=datetime.datetime.utcnow)
    content_text = StringField()

    # Champs IA
    summary = StringField()
    formulas = StringField()
    images_extracted = DictField()

    # Nouveau champ pour suivi
    processed = BooleanField(default=False)

    # Nouvelle miniature pour PDF / image
    thumbnail = StringField()

    meta = {
        'collection': 'resources',
        'ordering': ['-uploaded_at']
    }

    def generate_thumbnail(self, file_path):
        if file_path.endswith('.pdf') and not self.thumbnail:
            try:
                pages = convert_from_path(file_path, first_page=1, last_page=1)
                if pages:
                    buffer = BytesIO()
                    pages[0].save(buffer, format='PNG')
                    self.thumbnail = f"{os.path.splitext(os.path.basename(file_path))[0]}.png"
                    self.save()
            except Exception as e:
                print(f"Erreur génération miniature PDF : {e}")


def validate_file(value):
    valid_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.mp4']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f'Fichier non valide. Extensions autorisées: {valid_extensions}')
