"""
DealSense AI - Unified API Controller
Exposes all endpoints for the Car Lease/Loan Assistant.
"""

import os
import json
import re
import secrets
import logging
import tempfile
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Load env ──────────────────────────────────────────────────────────────────
load_dotenv()

# ── Gemini setup ──────────────────────────────────────────────────────────────
GEMINI_AVAILABLE = False
gemini_client = None
try:
    from google import genai
    _key = os.getenv("GEMINI_API_KEY")
    if _key:
        gemini_client = genai.Client(api_key=_key)
        GEMINI_AVAILABLE = True
except ImportError:
    pass

# ── Groq setup ────────────────────────────────────────────────────────────────
GROQ_AVAILABLE = False
groq_client = None
try:
    from groq import Groq
    _groq_key = os.getenv("GROQ_API_KEY")
    if _groq_key:
        groq_client = Groq(api_key=_groq_key)
        GROQ_AVAILABLE = True
except ImportError:
    pass

# ── Local imports ─────────────────────────────────────────────────────────────
from .vin_decoder import decode_vin_nhtsa
from .valuation import estimate_fair_price
from .ocr import process_generic_file
from .negotiation import NegotiationEngine

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Gemini available: {GEMINI_AVAILABLE}")
logger.info(f"Groq available:   {GROQ_AVAILABLE}")

# ── App & CORS ────────────────────────────────────────────────────────────────
app = FastAPI(title="DealSense AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global negotiator ─────────────────────────────────────────────────────────
negotiator = NegotiationEngine()

# ── Auth store ────────────────────────────────────────────────────────────────
USERS = {
    "admin": "admin123",
    "demo":  "demo123",
}
active_tokens: Dict[str, str] = {}   # token -> username


# ── Request Models ────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    context: Dict[str, Any]
    session_id: str = "default"


# ─────────────────────────────────────────────────────────────────────────────
# AUTH HELPER
# ─────────────────────────────────────────────────────────────────────────────
def get_username_from_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    return active_tokens.get(token)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: GET /
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "DealSense AI API is running"}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: POST /api/login
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/login")
def login(request: LoginRequest):
    """Validate credentials and return a session token."""
    expected = USERS.get(request.username)
    if not expected or expected != request.password:
        return {"success": False, "error": "Incorrect username or password."}

    token = secrets.token_hex(32)
    active_tokens[token] = request.username
    logger.info(f"✅ User '{request.username}' logged in")
    return {"success": True, "token": token, "username": request.username}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: POST /api/logout
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/logout")
def logout(authorization: Optional[str] = Header(None)):
    """Invalidate a session token."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        user = active_tokens.pop(token, None)
        if user:
            logger.info(f"User '{user}' logged out")
    return {"success": True, "message": "Logged out"}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: GET /api/verify
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/verify")
def verify_token(authorization: Optional[str] = Header(None)):
    """Check if a token is still valid."""
    username = get_username_from_token(authorization)
    if not username:
        return {"success": False, "error": "Invalid or expired token"}
    return {"success": True, "username": username}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: GET /api/market_value?vin=...&mileage=...
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/market_value")
def get_market_value(
    vin: str = Query(...),
    mileage: int = Query(12000),
):
    decoded = decode_vin_nhtsa(vin)
    if not decoded.get("success"):
        return {"success": False, "error": f"VIN Decode Failed: {decoded.get('error')}"}

    year  = decoded.get("year")
    make  = decoded.get("make")
    model = decoded.get("model")
    trim  = decoded.get("trim")

    if not all([year, make, model]):
        return {"success": False, "error": "Could not extract Year/Make/Model from VIN."}

    valuation = estimate_fair_price(year, make, model, mileage, vin=vin)
    if not valuation.get("success"):
        return {"success": False, "error": f"Valuation Failed: {valuation.get('error')}"}

    estimated_price = valuation.get("estimated_price", 0) or 0

    return {
        "success": True,
        "input": {"vin": vin, "mileage": mileage},
        "vehicle_details": {
            "year": year, "make": make, "model": model, "trim": trim,
            "type": decoded.get("vehicle_type"),
            "body_class": decoded.get("body_class"),
            "manufacturer": decoded.get("manufacturer"),
            "plant_country": decoded.get("plant_country"),
            "doors": decoded.get("doors"),
        },
        "engine_specs": {
            "cylinders": decoded.get("engine_cylinders"),
            "displacement_l": decoded.get("engine_displacement_l"),
            "horsepower": decoded.get("engine_hp"),
            "fuel_type": decoded.get("fuel_type"),
            "configuration": decoded.get("engine_config"),
        },
        "drivetrain": {
            "transmission": decoded.get("transmission"),
            "transmission_speeds": decoded.get("transmission_speeds"),
            "drive_type": decoded.get("drive_type"),
        },
        "safety_features": {
            "abs": decoded.get("abs"),
            "airbags": decoded.get("airbags"),
            "traction_control": decoded.get("traction_control"),
            "esc": decoded.get("esc"),
            "backup_camera": decoded.get("backup_camera"),
            "blind_spot_monitor": decoded.get("blind_spot_monitor"),
            "lane_departure_warning": decoded.get("lane_departure_warning"),
            "forward_collision_warning": decoded.get("forward_collision_warning"),
        },
        "ev_hybrid_info": {
            "electrification_level": decoded.get("electrification_level"),
            "battery_kwh": decoded.get("battery_kwh"),
            "ev_range": decoded.get("ev_range"),
        },
        "market_value": {
            "price": estimated_price,
            "currency": valuation.get("currency", "USD"),
            "fair_price_range": {
                "low":  round(estimated_price * 0.9, 2),
                "high": round(estimated_price * 1.1, 2),
            },
        },
        "metadata": {
            "valuation_method": valuation.get("method"),
            "source": "NHTSA + MarketCheck/Depreciation",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: POST /api/chat
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/chat")
def chat(request: ChatRequest):
    response = negotiator.get_response(
        request.message,
        request.context,
        request.session_id,
    )
    history = negotiator.get_chat_history(request.session_id)
    return {"success": True, "response": response, "history": history}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: GET /api/chat/history?session_id=...
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/chat/history")
def get_chat_history(session_id: str = Query("default")):
    history = negotiator.get_chat_history(session_id)
    return {"success": True, "history": history}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: DELETE /api/chat/history?session_id=...
# ─────────────────────────────────────────────────────────────────────────────
@app.delete("/api/chat/history")
def clear_chat_history(session_id: str = Query("default")):
    negotiator.clear_chat_history(session_id)
    return {"success": True, "message": "Chat history cleared"}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: GET /api/vin_insights?vin=...
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/vin_insights")
def get_vin_insights(vin: str = Query(...)):
    try:
        decoded = decode_vin_nhtsa(vin)
        year  = decoded.get("year", "Unknown")
        make  = decoded.get("make", "Unknown")
        model = decoded.get("model", "Unknown")

        prompt = (
            f"You are a car negotiation expert. For a {year} {make} {model}, "
            f"provide exactly 3 short practical negotiation tips (one sentence each). "
            f"Also give days_on_market (integer 10-120) and market_position as one of: "
            f"above_market, at_market, below_market. "
            f"Respond ONLY with valid JSON, no markdown:\n"
            f'{{"days_on_market": 45, "market_position": "at_market", '
            f'"negotiation_tips": ["tip1", "tip2", "tip3"]}}'
        )

        raw = None

        # Try Gemini first
        if GEMINI_AVAILABLE and gemini_client:
            try:
                r = gemini_client.models.generate_content(
                    model="gemini-2.0-flash-lite", contents=prompt
                )
                raw = r.text.strip() if r and r.text else None
            except Exception as e:
                logger.warning(f"Gemini vin_insights failed: {e}")

        # Fallback to Groq
        if not raw and GROQ_AVAILABLE and groq_client:
            try:
                r = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                )
                raw = r.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"Groq vin_insights failed: {e}")

        if raw:
            raw = re.sub(r"^```(?:json)?", "", raw).strip()
            raw = re.sub(r"```$", "", raw).strip()
            insights = json.loads(raw)
            return {
                "success": True,
                "days_on_market":   insights.get("days_on_market"),
                "market_position":  insights.get("market_position"),
                "negotiation_tips": insights.get("negotiation_tips", []),
            }

    except Exception as e:
        logger.error(f"VIN insights failed: {e}")

    # Safe fallback
    return {
        "success": True,
        "days_on_market": None,
        "market_position": None,
        "negotiation_tips": [
            "Ask the dealer for their best out-the-door price first.",
            "Research competing listings to use as leverage.",
            "Negotiate the total price, not just the monthly payment.",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE: POST /api/document/analyze
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/document/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
):
    temp_path = None
    try:
        suffix   = os.path.splitext(file.filename or "upload")[1] or ".tmp"
        contents = await file.read()

        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        with open(temp_path, "wb") as f:
            f.write(contents)

        logger.info(f"Analyzing document: {file.filename} | prompt: {prompt}")

        # ── Step 1: Extract text via pdfplumber (best for digital PDFs) ───────
        extracted_text = ""
        try:
            import pdfplumber
            with pdfplumber.open(temp_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
            logger.info(f"pdfplumber extracted: {len(extracted_text)} chars")
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")

        # ── Step 2: Fallback to OCR if pdfplumber got nothing ─────────────────
        if not extracted_text.strip():
            ocr_result     = process_generic_file(temp_path)
            extracted_text = ocr_result.get("text", "").strip()
            logger.info(f"OCR extracted: {len(extracted_text)} chars")

        if not extracted_text.strip():
            return {
                "success": False,
                "error": "Could not extract text. Please upload a clearer image or PDF.",
            }

        # ── Step 3: AI analysis ───────────────────────────────────────────────
        question = prompt or "Extract and summarize all key information from this car document."
        ai_prompt = f"""You are a car negotiation expert analyzing a dealer document.

USER QUESTION: {question}

DOCUMENT TEXT:
{extracted_text[:4000]}

Tasks:
- Identify document type (window sticker, buyer's order, invoice, etc.)
- Extract: VIN, Year, Make, Model, Trim, Price, Fees, Add-ons
- Flag any hidden fees, dealer markups, or red flags
- Give specific negotiation advice based on the document"""

        response_text = None

        # Try Groq first (faster, generous free tier)
        if GROQ_AVAILABLE and groq_client:
            try:
                r = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": ai_prompt}],
                    max_tokens=1000,
                )
                response_text = r.choices[0].message.content.strip()
                logger.info(f"✅ Groq document response: {len(response_text)} chars")
            except Exception as e:
                logger.warning(f"Groq document analysis failed: {e}")

        # Fallback to Gemini
        if not response_text and GEMINI_AVAILABLE and gemini_client:
            try:
                r = gemini_client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=ai_prompt,
                )
                response_text = r.text.strip() if r and r.text else None
                logger.info(f"✅ Gemini document response: {len(response_text)} chars")
            except Exception as e:
                logger.warning(f"Gemini document analysis failed: {e}")

        if response_text:
            return {"success": True, "response": response_text, "is_conversation": True}

        # Final fallback — return raw extracted text
        return {
            "success": False,
            "error": "AI service unavailable. Please try again later.",
        }

    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass