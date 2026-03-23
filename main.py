from fastapi import FastAPI, UploadFile
import PyPDF2
import re

app = FastAPI()

@app.get("/")
def home():
    return {"message": "AI Car Contract Assistant is running"}

@app.post("/upload/")
async def upload_file(file: UploadFile):
    content = await file.read()

    # Save uploaded file
    with open("temp.pdf", "wb") as f:
        f.write(content)

    # Read PDF
    reader = PyPDF2.PdfReader("temp.pdf")
    text = ""

    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()

    #  Extraction logic
    apr = re.findall(r'\d+\.?\d*%', text)
    payment = re.findall(r'[\$₹]\s?\d+', text)
    duration = re.findall(r'\d+\s*(months|years)', text, re.IGNORECASE)
    penalty = re.findall(r'penalty.*', text, re.IGNORECASE)

    # Clean Output
    result = {
        "Summary": {
            "APR": apr if apr else ["Not Found"],
            "Monthly Payment": payment if payment else ["Not Found"],
            "Duration": duration if duration else ["Not Found"],
            "Penalty": penalty if penalty else ["Not Found"]
        },
        "Message": "Extraction completed successfully"
    }

    return result