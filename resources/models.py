from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
import os
from io import BytesIO
from pdf2image import convert_from_path  # pip install pdf2image

RESOURCE_TYPES = [
    ('PDF', 'PDF'),
    ('VIDEO', 'Vidéo'),
    ('IMAGE', 'Image'),
]

def validate_file(file):
    max_size_mb = 500  # 500 Mo max
    ext_allowed = ['pdf', 'mp4', 'png', 'jpg', 'jpeg']
    ext = file.name.split('.')[-1].lower()
    if ext not in ext_allowed:
        raise ValidationError(f"Le type de fichier .{ext} n'est pas autorisé.")
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Le fichier dépasse {max_size_mb} Mo.")

class Resource(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='resources/', validators=[validate_file])
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    tags = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    content_text = models.TextField(blank=True, null=True)

    # Champs IA
    summary = models.TextField(blank=True)
    formulas = models.TextField(blank=True)
    images_extracted = models.JSONField(blank=True, null=True)

    # Nouveau champ pour suivi
    processed = models.BooleanField(default=False)

    # Nouvelle miniature pour PDF / image
    thumbnail = models.ImageField(upload_to='resources/thumbnails/', blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Générer une miniature si c'est un PDF et qu'il n'y a pas encore de thumbnail
        if self.file and self.file.url.endswith('.pdf') and not self.thumbnail:
            try:
                pages = convert_from_path(self.file.path, first_page=1, last_page=1)
                if pages:
                    buffer = BytesIO()
                    pages[0].save(buffer, format='PNG')
                    self.thumbnail.save(f'{os.path.splitext(os.path.basename(self.file.name))[0]}.png',
                                        ContentFile(buffer.getvalue()), save=False)
                    super().save(update_fields=['thumbnail'])
            except Exception as e:
                print(f"Erreur génération miniature PDF : {e}")

    def __str__(self):
        return self.title
