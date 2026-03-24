import os
import json
import tempfile
from pathlib import Path
from io import BytesIO
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import easyocr
import uvicorn
from risk_scorer import LeaseRiskScorer

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Lease Extractor API")

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Enable CORS (for frontend requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Memory to store last uploaded document info
document_memory = {
    "text": "",             # raw document text
    "structured_data": None, # extracted JSON
    "source_type": None,     # pdf or image
    "filename": None         # original filename
}

IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff"
}

_ocr_reader = None


def _get_ocr_reader():
    """Lazily initialize EasyOCR reader to avoid repeated heavy loads."""
    global _ocr_reader
    if _ocr_reader is None:
        languages = [lang.strip() for lang in os.getenv("EASYOCR_LANGUAGES", "en").split(",") if lang.strip()]
        use_gpu = os.getenv("EASYOCR_USE_GPU", "false").lower() == "true"
        _ocr_reader = easyocr.Reader(languages or ["en"], gpu=use_gpu)
    return _ocr_reader


def describe_source(source_type: Optional[str]) -> str:
    if source_type == "pdf":
        return "PDF"
    if source_type == "image":
        return "image-based document"
    return "document"


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    text_chunks = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_chunks.append(page_text.strip())
    return "\n".join(text_chunks).strip()


def extract_text_from_image(file_bytes: bytes, filename: Optional[str] = None) -> str:
    suffix = os.path.splitext(filename or "upload")[1] or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        reader = _get_ocr_reader()
        text_fragments = reader.readtext(temp_path, detail=0, paragraph=True)
    finally:
        os.unlink(temp_path)

    return "\n".join(fragment.strip() for fragment in text_fragments if fragment and fragment.strip()).strip()


@app.post("/extract-lease/")
async def extract_lease(file: UploadFile = File(...)):
    file_bytes = await file.read()
    content_type = file.content_type or ""

    if content_type == "application/pdf":
        text = extract_text_from_pdf(file_bytes)
        source_type = "pdf"
    elif content_type in IMAGE_CONTENT_TYPES:
        text = extract_text_from_image(file_bytes, file.filename)
        source_type = "image"
    else:
        return {"error": "Unsupported file type. Upload a PDF or image (JPEG/PNG/WebP/BMP/TIFF)."}

    if not text:
        return {"status": "error", "message": "No text could be extracted from the document."}

    # Store raw document text
    document_memory["text"] = text
    document_memory["source_type"] = source_type
    document_memory["filename"] = file.filename

    document_label = describe_source(source_type)

    prompt = f"""
Extract the following details from this car lease agreement {document_label}.
Return ONLY valid JSON. Include all fields even if unknown (use null).

Fields:
- Agreement Number
- Date of Agreement
- Lessor Name
- Lessor Contact
- Lessee Name
- Lessee Contact
- Vehicle Brand
- Vehicle Model
- Vehicle VIN
- Lease Amount
- Monthly Payment
- Interest Rate
- Tenure
- Allowed Mileage
- Excess Mileage Fee
- Insurance Requirement
- Maintenance Responsibility
- Early Termination Fee
- Signatures
- Notes

Document:
{text}
"""

    response = client.chat.completions.create(
        model="arcee-ai/trinity-mini:free",
        messages=[
            {
                "role": "system",
                "content": "You are a legal document extraction assistant. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    output = response.choices[0].message.content

    try:
        structured_data = json.loads(output)
        # Store structured JSON in memory
        document_memory["structured_data"] = structured_data

        return {
            "status": "success",
            "data": structured_data,
            "raw_text_stored": True
        }

    except json.JSONDecodeError:
        document_memory["structured_data"] = None
        return {"status": "error", "raw_output": output}


@app.post("/ask/")
async def ask_question(question: str = Body(...)):
    """
    Ask any question about the last uploaded PDF.
    Uses both structured JSON and raw PDF text.
    """
    if not document_memory["text"]:
        return {"status": "error", "message": "No document uploaded yet."}

    document_label = describe_source(document_memory["source_type"])
    document_name = document_memory["filename"] or "uploaded document"

    prompt = f"""
You are an expert AI assistant specialized in car lease agreements.

The user has uploaded a car lease {document_label} ({document_name}). Here is the extracted structured data (JSON):

{json.dumps(document_memory['structured_data'], indent=4)}

Here is the full text of the document:

{document_memory['text']}

Your job is to answer any questions the user asks about this lease agreement. 

Rules:
1. Always base your answers ONLY on the JSON and PDF text provided.
2. If the information is in the structured JSON, use that first.
3. If not in JSON, check the full PDF text for the answer.
4. If the information is not present anywhere, reply exactly: "Information not found in the document."
5. Keep answers clear, concise, and user-friendly.

User Question:
{question}
"""

    response = client.chat.completions.create(
        model="arcee-ai/trinity-mini:free",
        messages=[
            {"role": "system", "content": "You are a legal document assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    answer = response.choices[0].message.content
    return {"status": "success", "answer": answer}


@app.post("/generate-summary/")
async def generate_summary():
    """
    Generate a simple, easy-to-understand summary of the lease agreement.
    Converts complex lease documents into plain language.
    """
    if not document_memory["text"]:
        return {"status": "error", "message": "No lease document uploaded yet. Please upload a lease document first."}
    
    prompt = f"""You are an expert at explaining complex legal documents in simple, easy-to-understand language.

A user has uploaded a car lease agreement. Your job is to create a SHORT, CLEAR summary that explains:

1. **The Vehicle**: What car is being leased (make, model, year, VIN if available)
2. **Lease Duration**: How long the lease lasts
3. **Monthly Payment**: How much the customer pays each month
4. **Mileage Allowance**: How many miles they can drive per year
5. **Overage Charges**: What they pay for extra miles beyond the limit
6. **Early Termination**: What it costs to end the lease early
7. **Maintenance & Insurance**: Who pays for what
8. **Important Penalties**: Any other major fees or rules

FORMATTING RULES:
- Use a heading for each section
- Write in simple, plain English (avoid legal jargon)
- Use short sentences and bullet points when helpful
- Be SPECIFIC: include numbers, amounts, percentages, and dates
- Keep it to 200-300 words maximum
- Make it easy for a non-lawyer to understand

TONE: Friendly, clear, and helpful - like explaining to a friend

Lease Document:
{document_memory['text']}
"""
    
    try:
        response = client.chat.completions.create(
            model="arcee-ai/trinity-mini:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at explaining complex legal documents in simple, plain English."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )
        
        summary = response.choices[0].message.content
        return {
            "status": "success",
            "summary": summary
        }
    except Exception as e:
        return {"status": "error", "message": f"Error generating summary: {str(e)}"}


@app.post("/calculate-risk/")
async def calculate_risk():
    """
    Calculate lease risk score based on previously extracted data.
    Uses the structured JSON data from the last uploaded document.
    """
    if not document_memory["structured_data"]:
        return {"status": "error", "message": "No lease data extracted yet. Please upload and extract a lease document first."}
    
    try:
        risk_result = LeaseRiskScorer.calculate_lease_risk(
            document_memory["structured_data"]
        )
        return risk_result
    except Exception as e:
        return {"status": "error", "message": f"Error calculating risk score: {str(e)}"}


@app.get("/", include_in_schema=False)
async def serve_homepage():
    """Serve the frontend homepage from the FastAPI server."""
    auth_page = FRONTEND_DIR / "auth.html"
    if auth_page.exists():
        return FileResponse(auth_page)
    return {"status": "error", "message": "Frontend not found. Ensure the frontend folder exists."}


# Mount frontend static files so auth/login/signup/index and assets load on port 8000.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
