import os
import pytesseract
from PIL import Image
import pdfplumber
from pdf2image import convert_from_path
import mysql.connector
from dotenv import load_dotenv

# Only needed on Windows or if Tesseract is not in PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".jpg", ".jpeg", ".png"]:
        try:
            img = Image.open(file_path)
            return pytesseract.image_to_string(img)
        except Exception as e:
            return f"Image OCR failed: {str(e)}"

    elif ext == ".pdf":
        text = ""

        # First try native text extraction (faster, better quality)
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {i+1} ---\n{page_text}\n"
        except Exception as e:
            text += f"\n(pdfplumber failed: {str(e)})\n"

        # Fallback to OCR if almost no text was extracted
        if len(text.strip()) < 300:  # rough heuristic
            try:
                pages = convert_from_path(
                    file_path,
                    poppler_path=r"C:\Users\User\Release-25.12.0-0\poppler-25.12.0\Library\bin"
                )
                for i, page_img in enumerate(pages):
                    page_text = pytesseract.image_to_string(page_img)
                    text += f"\n--- OCR Page {i+1} ---\n{page_text}\n"
            except Exception as e:
                text += f"\nOCR fallback failed: {str(e)}\n"

        return text  # hard limit to avoid token explosion

    return "Unsupported file type"


def store_in_mysql(file_path: str, extracted_text: str):
    load_dotenv()

    cursor = None
    conn = None
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME")
        )
        cursor = conn.cursor()

        file_name = os.path.basename(file_path)
        file_type = os.path.splitext(file_path)[1].lower()

        sql = """
        INSERT INTO documents (file_name, file_type, extracted_text)
        VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (file_name, file_type, extracted_text))
        conn.commit()

    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()