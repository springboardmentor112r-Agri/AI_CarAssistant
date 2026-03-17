import os
import json
import re
import logging
import tempfile
from typing import Dict, Any, Optional

from google import genai
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Load env & configure Gemini ──────────────────────────────────────────────
load_dotenv()
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ────────────────────────────────────────────────────────
# ── Local imports ─────────────────────────────────────────────────────────────
from .vin_decoder import decode_vin_nhtsa
from .valuation import estimate_fair_price
from .ocr import process_generic_file
from .negotiation import NegotiationEngine

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App & CORS ────────────────────────────────────────────────────────────────
app = FastAPI(title="Car Loan AI Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global negotiator ─────────────────────────────────────────────────────────
negotiator = NegotiationEngine()


# ── Request Models ────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str                    # frontend sends "message" (NOT "user_message")
    context: Dict[str, Any]
    session_id: str = "default"


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 1 — GET /api/market_value?vin=...&mileage=...
# app.js line: fetch(`${API_BASE}/api/market_value?vin=${encodeURIComponent(vin)}`)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/market_value")
def get_market_value(
    vin: str = Query(..., description="Vehicle Identification Number"),
    mileage: int = Query(12000, description="Vehicle mileage"),
):
    """Decode VIN via NHTSA and return vehicle details + market valuation."""

    # 1. Decode VIN
    decoded = decode_vin_nhtsa(vin)
    if not decoded.get("success"):
        return {
            "success": False,
            "error": f"VIN Decode Failed: {decoded.get('error')}",
        }

    year  = decoded.get("year")
    make  = decoded.get("make")
    model = decoded.get("model")
    trim  = decoded.get("trim")

    if not all([year, make, model]):
        return {
            "success": False,
            "error": "Could not extract Year/Make/Model from VIN.",
        }

    # 2. Valuation
    valuation = estimate_fair_price(year, make, model, mileage, vin=vin)
    if not valuation.get("success"):
        return {
            "success": False,
            "error": f"Valuation Failed: {valuation.get('error')}",
        }

    estimated_price = valuation.get("estimated_price", 0) or 0

    return {
        "success": True,
        "input": {"vin": vin, "mileage": mileage},
        "vehicle_details": {
            "year":          year,
            "make":          make,
            "model":         model,
            "trim":          trim,
            "type":          decoded.get("vehicle_type"),
            "body_class":    decoded.get("body_class"),
            "manufacturer":  decoded.get("manufacturer"),
            "plant_country": decoded.get("plant_country"),
            "doors":         decoded.get("doors"),
        },
        "engine_specs": {
            "cylinders":      decoded.get("engine_cylinders"),
            "displacement_l": decoded.get("engine_displacement_l"),
            "horsepower":     decoded.get("engine_hp"),
            "fuel_type":      decoded.get("fuel_type"),
            "configuration":  decoded.get("engine_config"),
        },
        "drivetrain": {
            "transmission":         decoded.get("transmission"),
            "transmission_speeds":  decoded.get("transmission_speeds"),
            "drive_type":           decoded.get("drive_type"),
        },
        "safety_features": {
            "abs":                       decoded.get("abs"),
            "airbags":                   decoded.get("airbags"),
            "traction_control":          decoded.get("traction_control"),
            "esc":                       decoded.get("esc"),
            "backup_camera":             decoded.get("backup_camera"),
            "blind_spot_monitor":        decoded.get("blind_spot_monitor"),
            "lane_departure_warning":    decoded.get("lane_departure_warning"),
            "forward_collision_warning": decoded.get("forward_collision_warning"),
        },
        "ev_hybrid_info": {
            "electrification_level": decoded.get("electrification_level"),
            "battery_kwh":           decoded.get("battery_kwh"),
            "ev_range":              decoded.get("ev_range"),
        },
        "market_value": {
            "price":    estimated_price,
            "currency": valuation.get("currency", "USD"),
            "fair_price_range": {
                "low":  round(estimated_price * 0.9, 2),
                "high": round(estimated_price * 1.1, 2),
            },
        },
        "metadata": {
            "valuation_method": valuation.get("method"),
            "source":           "NHTSA + MarketCheck/Depreciation",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 2 — POST /api/chat
# app.js sends: { message: text, context: currentContext, session_id: sessionId }
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/chat")
def chat(request: ChatRequest):
    """Chat with the AI negotiation assistant."""
    response = negotiator.get_response(
        request.message,        # frontend field is "message"
        request.context,
        request.session_id,
    )
    history = negotiator.get_chat_history(request.session_id)
    return {
        "success":  True,
        "response": response,
        "history":  history,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 3 — GET /api/chat/history?session_id=...
# app.js line: fetch(`${API_BASE}/api/chat/history?session_id=...`)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/chat/history")
def get_chat_history(session_id: str = Query("default")):
    """Return full chat history for a session."""
    history = negotiator.get_chat_history(session_id)
    return {"success": True, "history": history}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 4 — GET /api/vin_insights?vin=...
# app.js expects: { success, days_on_market, market_position, negotiation_tips }
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/vin_insights")
def get_vin_insights(vin: str = Query(..., description="Vehicle VIN")):
    """Return AI-generated negotiation insights for a vehicle."""
    try:
        decoded = decode_vin_nhtsa(vin)
        year  = decoded.get("year", "Unknown")
        make  = decoded.get("make", "Unknown")
        model = decoded.get("model", "Unknown")

        prompt = (
            f"You are a car negotiation expert. For a {year} {make} {model}, "
            f"provide exactly 3 short practical negotiation tips (one sentence each). "
            f"Also give an estimated days_on_market (integer between 10 and 120) "
            f"and market_position as exactly one of: above_market, at_market, below_market. "
            f"Respond ONLY with a valid JSON object, no markdown, no backticks:\n"
            f'{{"days_on_market": 45, "market_position": "at_market", '
            f'"negotiation_tips": ["tip1", "tip2", "tip3"]}}'
        )

        ai_response = gemini_client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
        )

        # Strip markdown fences if Gemini wraps in ```json
        raw = ai_response.text.strip()
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()

        insights = json.loads(raw)

        return {
            "success":          True,
            "days_on_market":   insights.get("days_on_market"),
            "market_position":  insights.get("market_position"),
            "negotiation_tips": insights.get("negotiation_tips", []),
        }

    except Exception as e:
        logger.error(f"VIN insights failed: {e}")
        # Safe fallback so the frontend card still shows something useful
        return {
            "success":          True,
            "days_on_market":   None,
            "market_position":  None,
            "negotiation_tips": [
                "Ask the dealer for their best out-the-door price first.",
                "Research competing listings to use as leverage.",
                "Negotiate the total price, not just the monthly payment.",
            ],
        }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 5 — POST /api/document/analyze  (multipart/form-data)
# app.js sends FormData with: file (File object), prompt (optional string)
# Frontend expects: { success, is_conversation?, response?, analysis? }
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/document/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
):
    """Analyze an uploaded document (PDF/image) with an optional user prompt."""
    temp_path = None
    try:
        suffix   = os.path.splitext(file.filename or "upload")[1] or ".tmp"
        contents = await file.read()

        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        with open(temp_path, "wb") as f:
            f.write(contents)

        logger.info(f"Analyzing document: {file.filename} | prompt: {prompt}")

        # 1. OCR extraction
        ocr_result     = process_generic_file(temp_path)
        extracted_text = ocr_result.get("text", "").strip()
        
        logger.info(f"OCR result keys: {ocr_result.keys()}")
        logger.info(f"Extracted text length: {len(extracted_text)}")
        logger.info(f"Extracted text preview: {extracted_text[:300]}")

        if not extracted_text:
            return {
                "success": False,
                "error":   "Could not extract text. Please upload a clearer image or PDF.",
            }

        # 2. AI analysis
        analysis_result = negotiator.analyze_document_text(extracted_text, prompt)
        return analysis_result

    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 6 — DELETE /api/chat/history?session_id=...
# ─────────────────────────────────────────────────────────────────────────────
@app.delete("/api/chat/history")
def clear_chat_history(session_id: str = Query("default")):
    """Clear chat history for a session."""
    negotiator.clear_chat_history(session_id)
    return {"success": True, "message": "Chat history cleared"}


# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Car Loan AI Assistant API is running"}
