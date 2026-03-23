"""
Pytesseract OCR fallback service.

Used when Google Vision API fails or is not configured.
Supports:
  - Images (JPG, PNG, TIFF, BMP, WEBP, HEIC) via Pillow + pytesseract
  - Scanned PDFs via pdf2image + pytesseract
"""

import io
import logging
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes

logger = logging.getLogger(__name__)


def ocr_image_bytes(file_bytes: bytes) -> str:
    """
    Run pytesseract OCR on raw image bytes.
    Returns extracted text or empty string on failure.
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        logger.warning(f"pytesseract image OCR failed: {e}")
        return ""


def ocr_pdf_bytes(file_bytes: bytes) -> str:
    """
    Convert a PDF to images and run pytesseract on each page.
    Returns concatenated text or empty string on failure.
    """
    try:
        images = convert_from_bytes(file_bytes)
        parts = []
        for page_num, image in enumerate(images, 1):
            page_text = pytesseract.image_to_string(image)
            if page_text and page_text.strip():
                parts.append(page_text.strip())
        return "\n\n".join(parts)
    except Exception as e:
        logger.warning(f"pytesseract PDF OCR failed: {e}")
        return ""
