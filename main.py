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
    return {"message": "DealGuard AI Running"}


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


def risk_level(risk: int):
    if risk > 50:
        return "High"
    elif risk > 20:
        return "Moderate"
    return "Low"


def verdict(risk: int):
    if risk > 50:
        return "Not Recommended"
    elif risk > 25:
        return "Proceed with Caution"
    return "Good Deal"


def insights(data: Dict, level: str):
    explanation = []
    suggestions = []

    if data["APR"]:
        explanation.append("Higher APR increases loan cost")
        suggestions.append("Negotiate lower interest rate")

    if data["Penalties"]:
        explanation.append("Penalty clauses increase financial burden")
        suggestions.append("Reduce penalty clauses")

    if data["RedFlags"]:
        explanation.append("Risky legal terms detected")

    if not data["Duration"]:
        suggestions.append("Ensure contract duration is defined")

    decision = (
        "Avoid this contract" if level == "High"
        else "Review carefully" if level == "Moderate"
        else "Safe to proceed"
    )

    return explanation, suggestions, decision


def summary(data: Dict):
    return f"Contract with APR {data['APR']} and duration {data['Duration']} shows {len(data['RedFlags'])} risk indicators."


def breakdown(data: Dict):
    items = []
    if data["APR"]:
        items.append("APR impacts total cost")
    if data["Penalties"]:
        items.append("Penalties increase burden")
    if data["RedFlags"]:
        items.append("Legal risks detected")
    return items


@app.post("/analyze/")
async def analyze(file: UploadFile):
    global last_analysis

    text = extract_text(await file.read())
    data = extract_data(text)

    score, risk = calculate_risk(data)
    level = risk_level(risk)
    v = verdict(risk)

    explanation, suggestions, decision = insights(data, level)

    result = {
        "APR": data["APR"] or ["Not Found"],
        "Payment": data["Payment"] or ["Not Found"],
        "Duration": data["Duration"] or ["Not Found"],
        "VIN": data["VIN"] or ["Not Found"],

        "Contract Quality Score": score,
        "Risk %": risk,
        "Risk Level": level,

        "Final Verdict": v,
        "Decision Guide": decision,

        "Why This Result": explanation,
        "Suggestions": suggestions,
        "Red Flags": data["RedFlags"] or ["None"],

        "Summary": summary(data),
        "Risk Breakdown": breakdown(data),

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
        "Reason": "Lower APR means lower financial cost"
    }


@app.get("/chat/")
def chat(query: str):
    q = query.lower()

    if last_analysis:
        if "risk" in q:
            return {"response": f"Risk level is {last_analysis['Risk Level']} with {last_analysis['Risk %']} percent risk"}

        if "good" in q or "verdict" in q:
            return {"response": f"System suggests: {last_analysis['Final Verdict']}"}

        if "suggest" in q:
            return {"response": f"Suggestions: {last_analysis['Suggestions']}"}

        if "summary" in q:
            return {"response": last_analysis["Summary"]}

    if "apr" in q:
        return {"response": "APR is the yearly interest rate"}

    return {"response": "Ask about risk, APR, or contract quality"}
