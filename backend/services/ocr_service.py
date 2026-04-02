import pdfplumber
import pytesseract
from PIL import Image
import os


def extract_text_from_file(file_path: str, ext: str) -> str:
    """Extract plain text from a PDF or image file."""
    try:
        if ext == ".pdf":
            return _extract_from_pdf(file_path)
        else:
            return _extract_from_image(file_path)
    except Exception as e:
        return f"[OCR Error: {str(e)}]"


def _extract_from_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
            else:
                # Fallback: render page as image and OCR
                img = page.to_image(resolution=200).original
                text_parts.append(pytesseract.image_to_string(img))
    return "\n".join(text_parts).strip()


def _extract_from_image(path: str) -> str:
    img = Image.open(path)
    return pytesseract.image_to_string(img).strip()
