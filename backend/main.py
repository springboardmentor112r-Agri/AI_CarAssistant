import os
import io
import json
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

# 🔑 Gemini API Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ✅ Working model
model = genai.GenerativeModel("gemini-2.5-flash")

# Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📄 OCR extraction
def extract_text_from_pdf(content: bytes) -> str:
    text = ""
    with fitz.open(stream=content, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text().strip()
            if page_text:
                text += page_text + "\n"
            else:
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes()))
                text += pytesseract.image_to_string(img) + "\n"
    return text


# 🤖 Gemini analysis
def analyze_with_llm(text: str):
    prompt = f"""
You are a strict financial contract analyzer.

Extract EXACT values from the contract.

Rules:
- APR may also be called "interest rate", "finance rate", or "rate of interest"
- DO NOT guess
- ALWAYS return valid JSON
- "risks" MUST be a list

Return ONLY JSON:

{{
  "apr": "percentage if found, else Not found",
  "monthly_payment": "amount with currency",
  "lease_term": "number of months",
  "risks": ["...", "..."]
}}

Contract:
{text[:1500]}
"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        raw = re.sub(r"```json|```", "", raw).strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)

        if match:
            data = json.loads(match.group())

            # Fix lease term
            term = data.get("lease_term")
            if isinstance(term, int):
                data["lease_term"] = f"{term} months"
            elif isinstance(term, str) and term.isdigit():
                data["lease_term"] = term + " months"

            # Ensure risks is list
            if isinstance(data.get("risks"), str):
                data["risks"] = [data["risks"]]

            return data

    except Exception as e:
        return {
            "apr": "Error",
            "monthly_payment": "Error",
            "lease_term": "Error",
            "risks": [str(e)]
        }

    return {
        "apr": "Not found",
        "monthly_payment": "Not found",
        "lease_term": "Not found",
        "risks": ["Could not parse"]
    }


# 🧠 Decision Logic
def evaluate_contract(analysis: dict):
    score = 100
    risks = analysis.get("risks", [])

    # Risk penalty
    if len(risks) >= 2:
        score -= 20
    elif len(risks) == 1:
        score -= 10

    # High payment penalty
    payment = analysis.get("monthly_payment", "")
    try:
        amount = int(payment.replace("₹", "").replace(",", "").strip())
        if amount > 50000:
            score -= 15
    except:
        pass

    # Missing APR penalty
    if analysis.get("apr") == "Not found":
        score -= 10

    score = max(0, min(score, 100))

    # Risk level
    if score >= 75:
        risk_level = "Low"
    elif score >= 50:
        risk_level = "Medium"
    else:
        risk_level = "High"

    summary = f"This contract has a {risk_level.lower()} risk level with a fairness score of {score}/100."

    return {
        "risk_level": risk_level,
        "fairness_score": score,
        "summary": summary
    }

def generate_suggestions(analysis: dict, evaluation: dict):
    suggestions = []

    # High payment
    payment = analysis.get("monthly_payment", "")
    try:
        amount = int(payment.replace("₹", "").replace(",", "").strip())
        if amount > 50000:
            suggestions.append("Try negotiating the monthly payment — it seems relatively high.")
    except:
        pass

    # Risks
    for risk in analysis.get("risks", []):
        if "mileage" in risk.lower():
            suggestions.append("Ask for a higher mileage limit or reduced excess mileage charges.")

        if "penalty" in risk.lower():
            suggestions.append("Clarify or negotiate penalty clauses to avoid unexpected costs.")

    # Missing APR
    if analysis.get("apr") == "Not found":
        suggestions.append("Ask the dealer to clearly disclose the interest rate (APR).")

    # General
    if evaluation.get("risk_level") == "High":
        suggestions.append("Consider comparing this deal with other options before signing.")

    return suggestions

# 🚀 API endpoint
@app.post("/analyze")
async def analyze_contract(file: UploadFile = File(...)):
    try:
        content = await file.read()

        # OCR
        if file.filename.lower().endswith(".pdf"):
            extracted_text = extract_text_from_pdf(content)
        else:
            image = Image.open(io.BytesIO(content))
            extracted_text = pytesseract.image_to_string(image)

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text extracted")

        # ✅ FIXED FLOW
        analysis = analyze_with_llm(extracted_text)
        evaluation = evaluate_contract(analysis)
        suggestions = generate_suggestions(analysis, evaluation)

        return {
            "analysis": analysis,
            "evaluation": evaluation,
            "suggestions": suggestions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/chat")
async def chat_endpoint(request: dict):
    try:
        context = request.get("context")
        message = request.get("message")

        reply = chat_with_contract(context, message)

        return {
            "reply": reply
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def chat_with_contract(context: dict, user_message: str):
    prompt = f"""
You are a helpful car contract advisor.

Here is the contract analysis:
{json.dumps(context, indent=2)}

User question:
{user_message}

Instructions:
- Answer in simple language
- Be helpful and practical
- Give clear advice
- Keep it concise

Answer:
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# ▶️ Run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
