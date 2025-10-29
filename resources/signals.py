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

# Chemins
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"C:\Users\Lenovo\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin"

@receiver(post_save, sender=Resource)
def extract_text(sender, instance, created, **kwargs):
    if not instance.file:
        print(f"❌ La ressource {instance.title} n'a pas de fichier attaché")
        return

    file_rel_path = instance.file.name if hasattr(instance.file, 'name') else str(instance.file)
    file_path = os.path.join(settings.MEDIA_ROOT, file_rel_path)

    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé : {file_path}")
        return

    if instance.processed:
        print(f"ℹ️ Ressource déjà traitée : {instance.title}")
        return

    text = ""
    ext = os.path.splitext(file_path)[1].lower()
    print(f"ℹ️ Traitement du fichier : {file_path}, extension : {ext}")

    try:
        if ext == ".pdf":
            try:
                text = pdf_extract_text(file_path)
            except Exception as e:
                print(f"⚠️ Erreur pdfminer : {e}")
                text = ""

            if not text.strip():
                pages = convert_from_path(file_path, dpi=200, poppler_path=poppler_path)
                for page in pages:
                    text += pytesseract.image_to_string(page, lang='fra+eng') + "\n"

        elif ext in [".png", ".jpg", ".jpeg"]:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='fra+eng')

        # **NE PLUS GÉNÉRER LE RÉSUMÉ ICI**
        Resource.objects(id=instance.id).update(
            set__content_text=text.strip(),
            set__processed=True
        )

        print(f"✅ Extraction terminée pour {instance.title}. Longueur texte : {len(text)}")

    except Exception as e:
        print(f"❌ Erreur OCR pour {instance.file}: {e}")
