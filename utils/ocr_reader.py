import pytesseract
from PIL import Image

def extract_text_from_image(file_path):

    image = Image.open(file_path)

    text = pytesseract.image_to_string(image)

    return text