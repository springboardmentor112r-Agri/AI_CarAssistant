from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import re

app = FastAPI()

#  CORS (IMPORTANT FOR FRONTEND)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  PDF TEXT EXTRACTION 
def extract_text(file):
    reader = PyPDF2.PdfReader(file.file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


#  DATA EXTRACTION 
def extract_data(text):
    apr = re.search(r'(\d+(\.\d+)?)\s*%', text)
    monthly = re.search(r'(\d{2,6})\s*/?\s*month', text.lower())
    duration = re.search(r'(\d{1,3})\s*months', text.lower())
    vin = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', text)

    return {
        "apr": float(apr.group(1)) if apr else None,
        "monthly_payment": int(monthly.group(1)) if monthly else None,
        "duration": int(duration.group(1)) if duration else None,
        "vin": vin.group(0) if vin else None
    }


# RED FLAG DETECTION
def find_red_flags(text):
    flags = []
    keywords = ["penalty", "late fee", "default", "interest", "charge"]

    sentences = text.split(".")

    for line in sentences:
        for word in keywords:
            if word in line.lower():
                flags.append(line.strip())
                break

    return flags[:5] if flags else ["No major red flags detected"]


# RISK ANALYSIS
def analyze_risk(data):
    score = 100
    reasons = []
    suggestions = []

    if data["apr"] and data["apr"] > 10:
        score -= 25
        reasons.append("High interest rate")
        suggestions.append("Try negotiating a lower APR")

    if data["duration"] and data["duration"] > 60:
        score -= 20
        reasons.append("Long loan duration")
        suggestions.append("Choose shorter duration")

    if data["monthly_payment"] and data["monthly_payment"] > 20000:
        score -= 15
        reasons.append("High monthly payment")
        suggestions.append("Ensure EMI fits your budget")

    if not reasons:
        reasons.append("No major risks detected")
        suggestions.append("Contract looks balanced")

    risk_percent = 100 - score

    if score > 75:
        verdict = "Good Deal"
        level = "Low Risk"
        guide = "This contract is financially safe and balanced."
    elif score > 50:
        verdict = "Proceed with Caution"
        level = "Moderate Risk"
        guide = "Some conditions may increase cost. Review carefully."
    else:
        verdict = "Not Recommended"
        level = "High Risk"
        guide = "This contract has significant financial risk."

    return {
        "score": score,
        "risk_percent": risk_percent,
        "risk_level": level,
        "verdict": verdict,
        "reasons": reasons,
        "suggestions": suggestions,
        "decision_guide": guide
    }


#  ANALYZE 
@app.post("/analyze/")
async def analyze(file: UploadFile = File(...)):
    text = extract_text(file)

    data = extract_data(text)
    risk = analyze_risk(data)
    flags = find_red_flags(text)

    return {
        "analysis": risk,
        "red_flags": flags
    }


#  COMPARE 
@app.post("/compare/")
async def compare(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    t1 = extract_text(file1)
    t2 = extract_text(file2)

    r1 = analyze_risk(extract_data(t1))
    r2 = analyze_risk(extract_data(t2))

    if r1["score"] > r2["score"]:
        better = "Contract 1"
        reason = "Higher score and lower financial risk"
    else:
        better = "Contract 2"
        reason = "Better financial terms and lower risk"

    return {
        "better": better,
        "reason": reason
    }


# CHAT 
@app.post("/chat/")
async def chat(query: str = Form(...)):
    q = query.lower()

    if "apr" in q:
        return {"response": "APR is the annual interest rate of the loan."}
    elif "risk" in q:
        return {"response": "Risk shows how financially safe or unsafe the contract is."}
    elif "good" in q:
        return {"response": "A good contract has low APR, short duration, and affordable EMI."}
    elif "penalty" in q:
        return {"response": "Penalty clauses include late fees and extra charges."}
    else:
        return {"response": "Ask about APR, risk, penalties, or contract quality."}
