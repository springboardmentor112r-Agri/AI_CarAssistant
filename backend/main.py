from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import fitz  
import re
import shutil
import os
import requests
import uuid
from openai import OpenAI


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

contract_memory = {"text": ""}

@app.get("/")
def home():
    return {"message": "DealGuard Backend is officially LIVE and READY"}

def get_vehicle_details(vin):
    """Fetches comprehensive specs from NHTSA API."""
    if not vin or len(vin) < 17 or "not found" in vin.lower():
        return None
    try:
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
        res = requests.get(url, timeout=5)
        data = res.json().get("Results", [{}])[0]
        return {
            "make": data.get("Make"),
            "model": data.get("Model"),
            "year": data.get("ModelYear"),
            "body": data.get("BodyClass"),
            "fuel": data.get("FuelTypePrimary"),
            "drive": data.get("DriveType"),
            "cylinders": data.get("EngineCylinders"),
            "hp": data.get("EngineHP")
        }
    except:
        return None

def extract_vin_with_llm(text_sample):
    """Fallback: Uses AI to find the VIN if Regex grabs the title."""
    try:
        prompt = "Find the 17-character VIN in this text. Look for labels like 'VIN', 'Vehicle ID', or 'Serial Number'. Return ONLY the 17-character VIN string. Text: " + text_sample[:3000]
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": prompt}]
        )
        found_vin = response.choices[0].message.content.strip()
      
        match = re.search(r'[A-HJ-NPR-Z0-9]{17}', found_vin.upper())
        return match.group(0) if match else None
    except:
        return None

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_location = f"temp_{unique_filename}"
    
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        doc = fitz.open(file_location)
        text = "".join([page.get_text() for page in doc])
        doc.close()
        
        contract_memory["text"] = text
        
        
        clean_text = re.sub(r'\s+', '', text)
        vin_match = re.search(r'[A-HJ-NPR-Z0-9]{17}', clean_text)
        vin = vin_match.group(0) if vin_match else None
        
        
        if vin and any(word in vin for word in ["LEASE", "AGREE", "VEHIC"]):
            vin = None
        
        
        if not vin:
            vin = extract_vin_with_llm(text)
        
        final_vin = vin if vin else "Not Found"
        specs = get_vehicle_details(final_vin)
        
        
        score = 100
        t = text.lower()
        if "as-is" in t or "no warranty" in t: score -= 35
        if "non-refundable" in t: score -= 25
        if "assumes all risk" in t or "indemnify" in t: score -= 20

        return {
            "vin": final_vin,
            "fairness_score": max(0, score),
            "specs": specs
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)

@app.post("/chat/")
async def chat_assistant(message_data: dict):
    user_msg = message_data.get("message", "")
    prompt = f"Contract Content: {contract_memory['text'][:3000]}\nUser Question: {user_msg}\nRules: Plain text, NO markdown, NO stars, be concise."
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": prompt}]
        )
        return {"response": response.choices[0].message.content}
    except:
        return {"response": "I'm having trouble connecting to the AI. Please try again."}
