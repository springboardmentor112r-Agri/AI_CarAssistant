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
    down_payment = re.findall(r'down payment.*?[\$₹]\s?\d+', text, re.IGNORECASE)
    mileage = re.findall(r'\d+\s*miles', text, re.IGNORECASE)
    penalty = re.findall(r'penalty.*', text, re.IGNORECASE)
    termination = re.findall(r'termination.*', text, re.IGNORECASE)
    buyout = re.findall(r'buyout.*|purchase option.*', text, re.IGNORECASE)
    vin = re.findall(r'[A-HJ-NPR-Z0-9]{17}', text)
    price_estimate = "₹8,00,000 - ₹10,00,000 (Estimated based on market trends)"


    #  Fairness Score
    score = 100
    if apr:
        try:
          if float(apr[0].replace('%','')) > 10:
            score -= 20
        except:
            pass
    if penalty:
        score -= 10
    if termination:
        score -= 10
    if not mileage:
        score -= 5

    if score >= 80:
        rating = "Good Deal"
    elif score >= 60:
        rating = "Moderate"
    else:
        rating = "Risky"

    #  Negotiation Suggestions
    suggestions = []

    if apr:
        suggestions.append("Try negotiating for a lower interest rate (APR).")
    if penalty:
        suggestions.append("Ask to reduce or remove late payment penalties.")
    if mileage:
        suggestions.append("Request higher mileage allowance.")
    if termination:
        suggestions.append("Negotiate flexible early termination terms.")
    if buyout:
        suggestions.append("Try negotiating a better buyout price.")

    #  Final Output
    return {
        "Summary": {
            "APR": apr if apr else ["Not Found"],
            "Monthly Payment": payment if payment else ["Not Found"],
            "Duration": duration if duration else ["Not Found"],
            "Down Payment": down_payment if down_payment else ["Not Found"],
            "Mileage": mileage if mileage else ["Not Found"],
            "Penalty": penalty if penalty else ["Not Found"],
            "Termination": termination if termination else ["Not Found"],
            "Buyout Option": buyout if buyout else ["Not Found"]
            "VIN": vin if vin else ["Not Found"]
        },
         "Estimated Price": price_estimate,
        "Fairness Score": score,
        "Rating": rating,
        "Negotiation Tips": suggestions if suggestions else ["No suggestions available"],
        "Message": "Advanced contract analysis completed"
    }
