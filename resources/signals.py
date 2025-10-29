from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Resource
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pdfminer.high_level import extract_text as pdf_extract_text
from .ai_summary import generate_summary
import os
from django.conf import settings

# Chemin vers tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

@receiver(post_save, sender=Resource)
def extract_text(sender, instance, created, **kwargs):
    if instance.processed:
        return

    text = ""
    file_path = os.path.join(settings.MEDIA_ROOT, instance.file)
    ext = file_path.split('.')[-1].lower()

    try:
        if ext == 'pdf':
            try:
                text = pdf_extract_text(file_path)
            except Exception:
                text = ""
            if not text.strip():
                pages = convert_from_path(file_path, dpi=200)
                for page in pages:
                    text += pytesseract.image_to_string(page, lang='fra') + "\n"

        elif ext in ['png', 'jpg', 'jpeg']:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='fra')

        # ⚙️ Étape IA : Génération du résumé
        summary = generate_summary(text)

        # Mise à jour sécurisée sans relancer post_save
        Resource.objects(id=instance.id).update(
            set__content_text=text.strip(),
            set__summary=summary,
            set__processed=True
        )

    except Exception as e:
        print(f"Erreur OCR pour le fichier {instance.file}: {e}")
