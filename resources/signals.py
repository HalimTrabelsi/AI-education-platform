from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Resource
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pdfminer.high_level import extract_text as pdf_extract_text

# Chemin vers tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

@receiver(post_save, sender=Resource)
def extract_text(sender, instance, created, **kwargs):
    if instance.processed:
        return

    text = ""
    file_path = instance.file.path
    ext = file_path.split('.')[-1].lower()

    try:
        if ext == 'pdf':
            # Essayer d'abord d'extraire le texte natif du PDF
            try:
                text = pdf_extract_text(file_path)
            except Exception:
                text = ""
            # Si texte vide, c'est probablement un PDF scanné → OCR
            if not text.strip():
                pages = convert_from_path(file_path, dpi=200)
                for page in pages:
                    text += pytesseract.image_to_string(page, lang='fra') + "\n"

        elif ext in ['png', 'jpg', 'jpeg']:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='fra')

        elif ext == 'mp4':
            text = "" 

        # Sauvegarde sécurisée
        instance.content_text = text.strip()
        instance.processed = True
        instance.save(update_fields=['content_text', 'processed'])

    except Exception as e:
        print(f"Erreur OCR pour le fichier {instance.file.name}: {e}")
