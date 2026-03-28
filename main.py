from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import re
from typing import Dict, List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

last_analysis = {}

@app.get("/")
def home():
    return {"message": "AI Contract Intelligence System Running"}


def extract_text(file_bytes: bytes) -> str:
    try:
        with open("temp.pdf", "wb") as f:
            f.write(file_bytes)

        reader = PyPDF2.PdfReader("temp.pdf")
        text = ""

        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + " "

        return text.strip()
    except:
        raise HTTPException(status_code=500, detail="PDF processing failed")


def extract_data(text: str) -> Dict:
    return {
        "APR": re.findall(r'\d+\.?\d*%', text),
        "Payment": re.findall(r'[\$₹]\s?\d+(?:,\d+)*', text),
        "Duration": re.findall(r'\d+\s*(?:months|years)', text, re.IGNORECASE),
        "VIN": re.findall(r'[A-HJ-NPR-Z0-9]{17}', text),
        "Penalties": re.findall(r'penalty.*', text, re.IGNORECASE),
        "RedFlags": re.findall(r'penalty|termination|default|repossession', text, re.IGNORECASE)
    }


def get_apr_value(apr_list: List[str]):
    try:
        return float(apr_list[0].replace('%', ''))
    except:
        return None


def calculate_risk(data: Dict):
    score = 100
    apr_value = get_apr_value(data["APR"])

    if apr_value:
        if apr_value > 12:
            score -= 30
        elif apr_value > 8:
            score -= 15

    if data["Penalties"]:
        score -= 10

    if data["RedFlags"]:
        score -= 10

    score = max(score, 0)
    risk = 100 - score

    return score, risk


def get_risk_level(risk: int):
    if risk > 50:
        return "High"
    elif risk > 20:
        return "Moderate"
    return "Low"


def get_verdict(risk: int):
    if risk > 50:
        return "Not Recommended"
    elif risk > 25:
        return "Proceed with Caution"
    return "Good Deal"


def generate_insights(data: Dict, risk_level: str):
    explanation = []
    suggestions = []

    if data["APR"]:
        explanation.append("High APR increases loan cost")
        suggestions.append("Negotiate lower interest rate")

    if data["Penalties"]:
        explanation.append("Penalty clauses increase financial burden")
        suggestions.append("Reduce or remove penalties")

    if not data["Duration"]:
        suggestions.append("Ensure contract duration is defined")

    decision = (
        "Avoid this contract" if risk_level == "High"
        else "Review carefully" if risk_level == "Moderate"
        else "Safe to proceed"
    )

    return explanation, suggestions, decision


@app.post("/analyze/")
async def analyze(file: UploadFile):
    global last_analysis

    text = extract_text(await file.read())
    data = extract_data(text)

    score, risk = calculate_risk(data)
    risk_level = get_risk_level(risk)
    verdict = get_verdict(risk)

    explanation, suggestions, decision = generate_insights(data, risk_level)

    result = {
        "APR": data["APR"] or ["Not Found"],
        "Payment": data["Payment"] or ["Not Found"],
        "Duration": data["Duration"] or ["Not Found"],
        "VIN": data["VIN"] or ["Not Found"],
        "Contract Quality Score": score,
        "Risk %": risk,
        "Risk Level": risk_level,
        "Final Verdict": verdict,
        "Decision Guide": decision,
        "Why This Result": explanation,
        "Suggestions": suggestions,
        "Red Flags": data["RedFlags"] or ["None"],
        "Confidence Level": "High" if len(text) > 500 else "Medium"
    }

    last_analysis = result
    return result


@app.post("/compare/")
async def compare(file1: UploadFile, file2: UploadFile):
    text1 = extract_text(await file1.read())
    text2 = extract_text(await file2.read())

    apr1 = get_apr_value(re.findall(r'\d+\.?\d*%', text1))
    apr2 = get_apr_value(re.findall(r'\d+\.?\d*%', text2))

    if apr1 is None or apr2 is None:
        better = "Unable to determine"
    else:
        better = "Contract 1" if apr1 < apr2 else "Contract 2"

    return {
        "Better Contract": better,
        "Reason": "Lower APR indicates lower financial burden"
    }


@app.get("/chat/")
def chat(query: str):
    q = query.lower()

    if last_analysis:
        if "risk" in q:
            return {"response": f"The contract risk level is {last_analysis['Risk Level']} with {last_analysis['Risk %']} percent risk."}

        if "verdict" in q or "good" in q:
            return {"response": f"The system suggests: {last_analysis['Final Verdict']}"}

        if "issue" in q:
            return {"response": f"Key issues include: {last_analysis['Red Flags']}"}

        if "suggest" in q:
            return {"response": f"Suggestions: {last_analysis['Suggestions']}"}

    if "apr" in q:
        return {"response": "APR is the annual interest rate applied to the loan."}

    if "penalty" in q:
        return {"response": "Penalties are extra charges for violations in contract terms."}

    if "compare" in q:
        return {"response": "The better contract has lower APR and fewer penalties."}

    return {"response": "Ask about risk, APR, penalties, or contract evaluation."}
   
