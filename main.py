from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import re
from typing import List

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "AI Contract Intelligence System Running"}


# Utility 

def extract_text_from_pdf(content: bytes) -> str:
    try:
        with open("temp.pdf", "wb") as f:
            f.write(content)

        reader = PyPDF2.PdfReader("temp.pdf")
        text = ""

        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "

        return text.strip()

    except Exception:
        raise HTTPException(status_code=500, detail="Error processing PDF")


def extract_apr(text: str) -> List[str]:
    return re.findall(r'\d+\.?\d*%', text)


def extract_payment(text: str) -> List[str]:
    return re.findall(r'[\$₹]\s?\d+(?:,\d+)*', text)


def extract_duration(text: str) -> List[str]:
    return re.findall(r'\d+\s*(?:months|years)', text, re.IGNORECASE)


def extract_vin(text: str) -> List[str]:
    return re.findall(r'[A-HJ-NPR-Z0-9]{17}', text)


def extract_penalties(text: str) -> List[str]:
    return re.findall(r'penalty.*', text, re.IGNORECASE)


def extract_red_flags(text: str) -> List[str]:
    return re.findall(r'penalty|termination|default|repossession', text, re.IGNORECASE)


def safe_apr_value(apr_list: List[str]) -> float:
    try:
        return float(apr_list[0].replace('%', ''))
    except:
        return None

# Risk Calculation

def calculate_score(apr, penalties, red_flags):
    score = 100

    apr_value = safe_apr_value(apr)

    if apr_value:
        if apr_value > 12:
            score -= 30
        elif apr_value > 8:
            score -= 15

    if penalties:
        score -= 10

    if red_flags:
        score -= 10

    return max(score, 0)


def determine_risk_level(risk):
    if risk > 50:
        return "High"
    elif risk > 20:
        return "Moderate"
    return "Low"


def determine_verdict(risk):
    if risk > 50:
        return "Not Recommended"
    elif risk > 25:
        return "Proceed with Caution"
    return "Good Deal"


def financial_risk(apr):
    val = safe_apr_value(apr)
    if val and val > 10:
        return "High"
    return "Low"


def legal_risk(red_flags):
    return "High" if red_flags else "Low"


# Explanation + Suggestions

def generate_explanation(apr, penalties, red_flags):
    explanation = []

    if apr:
        explanation.append("Higher APR increases overall loan cost")

    if penalties:
        explanation.append("Penalty clauses increase financial burden")

    if red_flags:
        explanation.append("Risky legal terms detected in contract")

    return explanation


def generate_suggestions(apr, penalties, duration):
    suggestions = []

    if apr:
        suggestions.append("Try negotiating a lower interest rate")

    if penalties:
        suggestions.append("Request reduction or removal of penalties")

    if not duration:
        suggestions.append("Ensure contract duration is clearly defined")

    return suggestions


def key_issue(apr, penalties):
    if penalties:
        return "Penalty clause present"
    if apr:
        return "Interest rate is a key factor"
    return "No major issue"


def decision_guide(risk_level):
    if risk_level == "High":
        return "Avoid this contract"
    elif risk_level == "Moderate":
        return "Review carefully before signing"
    return "Safe to proceed"

# ANALYZE 

@app.post("/analyze/")
async def analyze(file: UploadFile):

    content = await file.read()
    text = extract_text_from_pdf(content)

    apr = extract_apr(text)
    payment = extract_payment(text)
    duration = extract_duration(text)
    vin = extract_vin(text)
    penalties = extract_penalties(text)
    red_flags = extract_red_flags(text)

    score = calculate_score(apr, penalties, red_flags)
    risk = 100 - score
    risk_level = determine_risk_level(risk)
    verdict = determine_verdict(risk)

    explanation = generate_explanation(apr, penalties, red_flags)
    suggestions = generate_suggestions(apr, penalties, duration)

    return {
        "APR": apr or ["Not Found"],
        "Payment": payment or ["Not Found"],
        "Duration": duration or ["Not Found"],
        "VIN": vin or ["Not Found"],

        "Contract Quality Score": score,
        "Risk %": risk,
        "Risk Level": risk_level,

        "Financial Risk": financial_risk(apr),
        "Legal Risk": legal_risk(red_flags),

        "Final Verdict": verdict,
        "Key Issue": key_issue(apr, penalties),

        "Why This Result": explanation,
        "Suggestions": suggestions,
        "Decision Guide": decision_guide(risk_level),

        "Red Flags": red_flags or ["None"],
        "Confidence Level": "High" if len(text) > 500 else "Medium"
    }
# COMPARE 

@app.post("/compare/")
async def compare(file1: UploadFile, file2: UploadFile):

    text1 = extract_text_from_pdf(await file1.read())
    text2 = extract_text_from_pdf(await file2.read())

    apr1 = extract_apr(text1)
    apr2 = extract_apr(text2)

    val1 = safe_apr_value(apr1)
    val2 = safe_apr_value(apr2)

    if val1 is None or val2 is None:
        better = "Unable to determine"
    else:
        better = "Contract 1" if val1 < val2 else "Contract 2"

    return {
        "Contract 1 APR": apr1 or ["Not Found"],
        "Contract 2 APR": apr2 or ["Not Found"],
        "Better Contract": better,
        "Reason": "Lower APR indicates lower financial burden"
    }


# CHAT 

@app.get("/chat/")
def chat(query: str):

    q = query.lower()

    if "risk" in q:
        return {"response": "Risk depends on interest rate and penalty clauses"}

    if "apr" in q:
        return {"response": "APR is the annual interest rate applied to the loan"}

    if "penalty" in q:
        return {"response": "Penalties are extra charges for violations in contract terms"}

    if "best contract" in q or "compare" in q:
        return {"response": "The better contract typically has lower APR and fewer penalties"}

    return {"response": "Ask about APR, risk, penalties, or comparison"}
