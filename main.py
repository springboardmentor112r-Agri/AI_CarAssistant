from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import json

from pdf_jpg_ocr import extract_text, store_in_mysql
from llm_engine import analyze_contract

app = FastAPI(title="Contract Review AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {"message": "Contract Review AI API is running"}


@app.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    # Generate safe unique filename
    original_name = file.filename
    safe_name = f"{uuid.uuid4()}_{original_name}"
    file_path = os.path.join(UPLOAD_FOLDER, safe_name)

    # Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return {"error": f"File save failed: {str(e)}"}

    # Extract text
    try:
        extracted_text = extract_text(file_path)
    except Exception as e:
        return {"error": f"Text extraction failed: {str(e)}"}

    # Store in DB
    store_in_mysql(file_path, extracted_text)

    # Analyze with LLM
    # Inside the /upload endpoint — around where you handle ai_raw_output

    ai_raw_output = analyze_contract(extracted_text)

    try:
        ai_json = json.loads(ai_raw_output)
    except json.JSONDecodeError as e:
        # Local models sometimes add ```json fencing or extra newlines
        cleaned = ai_raw_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1].strip() if len(cleaned.split("```")) > 2 else cleaned

        try:
            ai_json = json.loads(cleaned)
        except json.JSONDecodeError:
            ai_json = {
                "error": "Could not parse LLM output as JSON",
                "raw_output_preview": ai_raw_output[:800],
                "parse_error": str(e)
            }

    # Save analysis to file (optional but useful for debugging)
    analysis_path = os.path.join(UPLOAD_FOLDER, f"{safe_name}_analysis.json")
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(ai_json, f, indent=2, ensure_ascii=False)

    # Response for frontend
    return {
        "status": "success",
        "file_id": safe_name,
        "original_filename": original_name,
        "text_preview": extracted_text[:600] + "..." if len(extracted_text) > 600 else extracted_text,
        "analysis": ai_json,
        "analysis_file_saved": analysis_path
    }