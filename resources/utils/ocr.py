import pytesseract
from PIL import Image
from pdf2image import convert_from_path

# Chemin vers tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ocr_from_pdf(pdf_path, lang='fra'):
    pages = convert_from_path(pdf_path, 300)
    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page, lang=lang) + "\n"
    return text

def ocr_from_image(image_path, lang='fra'):
    return pytesseract.image_to_string(Image.open(image_path), lang=lang)
