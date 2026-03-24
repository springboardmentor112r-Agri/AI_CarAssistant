from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agents.vin_service import generate_vin_report
from fastapi.responses import JSONResponse
from groq import Groq
import os
from pathlib import Path
from PyPDF2 import PdfReader
from agents.coordinator_agent import process_contract

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()
contract_text_global = ""
extracted_fields_global = {}  # Store extracted fields here

class VinRequest(BaseModel):
    vin: str

# ---------------------------
# Define extract_text_from_file here
# ---------------------------
def extract_text_from_file(file_path: str) -> str:
    ext = file_path.lower().split('.')[-1]

    if ext == "pdf":
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    elif ext == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError("Unsupported file type")
    
# CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
STORAGE_FOLDER = "storage"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STORAGE_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Car Lease AI Assistant Backend is Running Successfully!"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    global contract_text_global
    global extracted_fields_global

    ext = file.filename.lower().split(".")[-1]

    if ext not in ["pdf", "txt"]:
        return JSONResponse(status_code=400, content={"detail": "Only PDF and TXT files are supported"})

    safe_name = Path(file.filename).name
    file_path = os.path.join(UPLOAD_FOLDER, safe_name)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Extract text
    contract_text_global = extract_text_from_file(file_path)

    # Process contract and extract structured fields
    analysis_result = process_contract(contract_text_global)
    extracted_fields_global = analysis_result.get("vehicle_data", {})  # Store extracted fields globally

    save_extracted_text(safe_name, contract_text_global)

    return {
        "sla_data": analysis_result.get("sla_data", {}),
        "vehicle_data": analysis_result.get("vehicle_data", {}),
        "vin": analysis_result.get("vin"),
        "validation_issues": analysis_result.get("validation_issues", []),
        "risk_report": analysis_result.get("risk_report", {})
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


def save_extracted_text(filename, text):
    path = os.path.join(STORAGE_FOLDER, f"{filename}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def answer_from_fields(question: str, fields: dict):
    """Try to answer from extracted fields first"""
    q = question.lower()

    mapping = {
        "make": ["make"],
        "model": ["model"],
        "vin": ["vehicle identification number", "vin"],
        "interest rate": ["interest rate", "apr"],
        "monthly payment": ["monthly payment"],
        "lease start": ["lease start date"],
        "lease end": ["lease end date"]
        # Add more field mappings as needed
    }

    for key, possible_fields in mapping.items():
        if key in q:
            for field in possible_fields:
                if field in fields and fields[field]:
                    return fields[field]
    return None

# @app.get("/price")
# async def get_price(
#     vin: str = Query(None),
#     make: str = Query(None),
#     model: str = Query(None),
#     year: int = Query(None)
# ):
#     """
#     Returns market-based estimated price using MarketCheck API.
#     Either VIN or Make/Model/Year must be provided.
#     Short VINs are allowed.
#     """
#     # Prepare vehicle_data dict
#     vehicle_data = {}
#     if vin:
#         vehicle_data["VIN"] = vin
#     if make:
#         vehicle_data["Make"] = make
#     if model:
#         vehicle_data["Model"] = model
#     if year:
#         vehicle_data["Model Year"] = year

#     if not vehicle_data:
#         return {"error": "Provide either VIN or Make/Model/Year."}

#     try:
#         # Call estimate_price with a single dict argument
#         price_estimation = estimate_price(vehicle_data)
#     except Exception as e:
#         return {"error": str(e)}

#     return {
#         "vehicle": vehicle_data,
#         "estimated_price": price_estimation
#     }

@app.post("/vin_report")
async def vin_report(vin_request: VinRequest):
    vin = vin_request.vin
    if not vin or len(vin) != 17:
        return JSONResponse(content={"error": "Invalid VIN"}, status_code=400)

    report = generate_vin_report(vin)
    return JSONResponse(content=report)

def contract_ai_assistant(contract_text, fields, question):
    """Fallback to LLM if answer is not in extracted fields"""


    field_answer = answer_from_fields(question, fields)
    if field_answer:
        return field_answer


    contract_text = contract_text[:12000]
    prompt = f"""
You are an AI contract assistant helping someone understand their car lease or loan contract.

INSTRUCTIONS:
- Answer using only the information provided in the contract
- Keep the response concise (3–5 lines), natural, and easy to understand
- Explain what the information means for the user in practical terms, not just values
- Stay focused on the question and include closely related details if helpful
- If the specific detail is not present in the contract:
1. Give a general explanation of the concept in simple terms (without assuming contract details)
2. If relevant, briefly mention what is typically considered standard or important to check
CONTRACT:
{contract_text}

USER QUESTION:
{question}

YOUR ANSWER (3-4 lines max):
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful contract assistant. You provide concise, accurate answers in 3-4 lines maximum using only contract information."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1 
    )

    answer = response.choices[0].message.content.strip()

    sentences = answer.split('.')
    if len(sentences) > 4:
        answer = '. '.join(sentences[:4]) + '.'
    
    return answer


@app.post("/chat")
def chat(data: dict):
    
    question = data.get("question", "")
    
    # Check if contract exists
    if contract_text_global == "":
        return {"answer": "⚠️ Please upload a contract first before asking questions."}
    
    # Check if question is empty
    if not question or question.strip() == "":
        return {"answer": "❓ Please ask a specific question about your contract."}
    
    # Get answer from assistant
    answer = contract_ai_assistant(contract_text_global, extracted_fields_global, question)
    
    return {"answer": answer}