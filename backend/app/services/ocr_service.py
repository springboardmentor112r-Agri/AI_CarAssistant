import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
from typing import List, Dict


def extract_text_from_pdf(file_path: str) -> List[Dict]:
    """
    Extract text from each page of a PDF.
    Returns list of {page_number, text, confidence}.
    """
    pages = []
    doc = fitz.open(file_path)

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Try direct text extraction first (faster for digital PDFs)
        text = page.get_text("text")

        if len(text.strip()) > 50:
            pages.append({
                "page_number": page_num + 1,
                "text": text.strip(),
                "confidence": 0.99,
            })
        else:
            # Fallback: render page as image and run OCR
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            ocr_text = " ".join([w for w in ocr_data["text"] if w.strip()])
            confidences = [int(c) for c in ocr_data["conf"] if c != "-1"]
            avg_conf = sum(confidences) / len(confidences) / 100 if confidences else 0.0

            pages.append({
                "page_number": page_num + 1,
                "text": ocr_text,
                "confidence": round(avg_conf, 2),
            })

    doc.close()
    return pages


def extract_text_from_image(file_path: str) -> List[Dict]:
    """Extract text from a single image file."""
    img = Image.open(file_path)
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    text = " ".join([w for w in ocr_data["text"] if w.strip()])
    confidences = [int(c) for c in ocr_data["conf"] if c != "-1"]
    avg_conf = sum(confidences) / len(confidences) / 100 if confidences else 0.0

    return [{"page_number": 1, "text": text, "confidence": round(avg_conf, 2)}]