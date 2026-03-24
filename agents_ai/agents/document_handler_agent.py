import os
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def extract_text_from_file(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    # If PDF
    if file_extension == ".pdf":
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        # If no text found → use OCR
        if not text.strip():
            return ocr_pdf(file_path)

        return text

    # If image
    elif file_extension in [".jpg", ".jpeg", ".png"]:
        return ocr_image(file_path)

    else:
        raise ValueError("Unsupported file format")


def ocr_pdf(file_path):
    pages = convert_from_path(file_path)
    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page)
    return text


def ocr_image(file_path):
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)
