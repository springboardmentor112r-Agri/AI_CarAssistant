import fitz  # PyMuPDF
import os

async def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a given PDF file using PyMuPDF.
    If the document relies heavily on images, an OCR approach (like Tesseract)
    can be integrated here as a fallback.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    extracted_text = ""
    try:
        # Open the PDF file
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            extracted_text += page.get_text("text") + "\n"
        doc.close()
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        raise e
        
    return extracted_text.strip()
