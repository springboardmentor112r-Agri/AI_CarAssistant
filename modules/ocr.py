import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image


def extract_text(file):

    text = ""

    if file.type == "application/pdf":

        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        if text.strip() == "":
            file.seek(0)
            images = convert_from_bytes(file.read())

            for img in images:
                img = img.convert("L")
                text += pytesseract.image_to_string(img, config="--psm 6")

    else:

        image = Image.open(file)
        image = image.convert("L")
        text = pytesseract.image_to_string(image, config="--psm 6")

    return text
