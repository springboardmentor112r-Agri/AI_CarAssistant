import os
import json
import tempfile
from io import BytesIO
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import easyocr
import uvicorn

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AI Lease Extractor API")

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


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
