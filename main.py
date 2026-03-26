from fastapi import FastAPI, UploadFile
import PyPDF2
import re

app = FastAPI()

@app.get("/")
def home():
    return {"message": "AI Contract Intelligence System Running"}


# CONTRACT ANALYSIS
@app.post("/analyze/")
async def analyze(file: UploadFile):

    content = await file.read()
    with open("temp.pdf", "wb") as f:
        f.write(content)

    reader = PyPDF2.PdfReader("temp.pdf")
    text = ""

    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()

    #  Extraction
    apr = re.findall(r'\d+\.?\d*%', text)
    payment = re.findall(r'[\$₹]\s?\d+', text)
    duration = re.findall(r'\d+\s*(months|years)', text, re.IGNORECASE)
    penalty = re.findall(r'penalty.*', text, re.IGNORECASE)
    vin = re.findall(r'[A-HJ-NPR-Z0-9]{17}', text)

    #  Red Flags
    red_flags = re.findall(r'penalty|termination|default|repossession', text, re.IGNORECASE)

    #  Score Calculation
    score = 100

    if apr:
        try:
            val = float(apr[0].replace('%',''))
            if val > 12:
                score -= 30
            elif val > 8:
                score -= 15
        except:
            pass

    if penalty:
        score -= 10

    if red_flags:
        score -= 10

    risk = 100 - score

    #  Risk Level
    if risk > 50:
        risk_level = "High"
    elif risk > 20:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    #  Risk Categories
    financial_risk = "Low"
    legal_risk = "Low"

    if apr:
        try:
            if float(apr[0].replace('%','')) > 10:
                financial_risk = "High"
        except:
            pass

    if red_flags:
        legal_risk = "High"

    #  Verdict
    if risk > 50:
        verdict = "Not Recommended"
    elif risk > 25:
        verdict = "Proceed with Caution"
    else:
        verdict = "Good Deal"

    #  Suggestions
    suggestions = []

    if apr:
        suggestions.append("Try negotiating a lower interest rate.")

    if penalty:
        suggestions.append("Request reduction or removal of penalties.")

    if red_flags:
        suggestions.append("Carefully review risky clauses.")

    if not duration:
        suggestions.append("Ensure contract duration is clearly defined.")

    #  Explanation
    explanation = []

    if apr:
        explanation.append("Higher APR increases loan cost.")

    if penalty:
        explanation.append("Penalty clauses increase financial burden.")

    if red_flags:
        explanation.append("Risky legal clauses detected.")

    #  Key Issue
    key_issue = "No major issue"
    if penalty:
        key_issue = "Penalty clause present"
    elif apr:
        key_issue = "Interest rate is a key factor"

    #  Summary
    summary_text = f"APR: {apr}, Payment: {payment}, Duration: {duration}"

    #  Decision Guide
    if risk_level == "High":
        decision_guide = "Avoid this contract."
    elif risk_level == "Moderate":
        decision_guide = "Review carefully before signing."
    else:
        decision_guide = "Safe to proceed."

    final_message = f"This contract is {risk_level} risk. {decision_guide}"

    #  Confidence
    confidence = "High" if len(text) > 500 else "Medium"

    return {
        "Readable Summary": summary_text,
        "APR": apr if apr else ["Not Found"],
        "Payment": payment if payment else ["Not Found"],
        "Duration": duration if duration else ["Not Found"],
        "VIN": vin if vin else ["Not Found"],
        "Contract Quality Score": score,
        "Risk %": risk,
        "Risk Level": risk_level,
        "Financial Risk": financial_risk,
        "Legal Risk": legal_risk,
        "Final Verdict": verdict,
        "Key Issue": key_issue,
        "Why This Result": explanation,
        "Decision Guide": decision_guide,
        "Final Message": final_message,
        "Red Flags": red_flags if red_flags else ["None"],
        "Suggestions": suggestions,
        "Confidence Level": confidence
    }


# CONTRACT COMPARISON

@app.post("/compare/")
async def compare(file1: UploadFile, file2: UploadFile):

    def extract(file):
        content = file.file.read()
        with open("temp.pdf", "wb") as f:
            f.write(content)
        reader = PyPDF2.PdfReader("temp.pdf")
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()
        return text

    t1 = extract(file1)
    t2 = extract(file2)

    apr1 = re.findall(r'\d+\.?\d*%', t1)
    apr2 = re.findall(r'\d+\.?\d*%', t2)

    def get_apr(val):
        try:
            return float(val[0].replace('%',''))
        except:
            return 999

    better = "Contract 1" if get_apr(apr1) < get_apr(apr2) else "Contract 2"

    return {
        "Contract 1 APR": apr1,
        "Contract 2 APR": apr2,
        "Better Contract": better,
        "Reason": "Lower APR is financially better"
    }


# CHATBOT

@app.get("/chat/")
def chat(query: str):

    q = query.lower()

    if "risk" in q:
        return {"response": "Risk depends on APR and penalty clauses."}

    elif "apr" in q:
        return {"response": "APR is the interest rate applied to the loan."}

    elif "penalty" in q:
        return {"response": "Penalties are additional charges for violations."}

    elif "best contract" in q:
        return {"response": "The best contract has lower APR and fewer penalties."}

    else:
        return {"response": "Ask about APR, risk, penalties, or comparison."}
