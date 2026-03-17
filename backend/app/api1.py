import os
import logging
import tempfile
from typing import Dict, Any, Optional

from google import genai
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Load env & configure Gemini ──────────────────────────────────────────────
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))# FIX 1: was genai.api_key = ...

# ── Local module imports (absolute, not relative) ────────────────────────────
# FIX 2: relative imports (from .module) break when the file is run directly.
# Use absolute imports instead. Adjust the package prefix to match your project structure.
from .vin_decoder import decode_vin_nhtsa
from .valuation import estimate_fair_price
from .ocr import process_generic_file
from .negotiation import NegotiationEngine

# ── Logging ──────────────────────────────────────────────────────────────────
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


# ── Request / Response models ─────────────────────────────────────────────────
class MarketPriceRequest(BaseModel):
    vin: str
    mileage: int = 12000


class ChatRequest(BaseModel):
    user_message: str
    context: Dict[str, Any]
    session_id: str = "default"


class ClearHistoryRequest(BaseModel):
    session_id: str = "default"


# ── Helper (not a route) ──────────────────────────────────────────────────────
def _build_market_price_response(vin: str, mileage: int) -> Dict[str, Any]:
    """
    Core logic for market-price lookup.
    Separated from the route so it can also be called internally.
    """
    # 1. Decode VIN
    decoded = decode_vin_nhtsa(vin)
    if not decoded.get("success"):
        return {
            "success": False,
            "error": f"VIN Decode Failed: {decoded.get('error')}",
            "stage": "VIN_DECODE",
        }

    year  = decoded.get("year")
    make  = decoded.get("make")
    model = decoded.get("model")
    trim  = decoded.get("trim")

    if not all([year, make, model]):
        return {
            "success": False,
            "error": "Could not extract Year/Make/Model from VIN.",
            "vin_data": decoded,
            "stage": "DATA_EXTRACTION",
        }

    # 2. Valuation
    valuation = estimate_fair_price(year, make, model, mileage, vin=vin)
    if not valuation.get("success"):
        return {
            "success": False,
            "error": f"Valuation Failed: {valuation.get('error')}",
            "vin_data": decoded,
            "stage": "VALUATION",
        }

    estimated_price = valuation.get("estimated_price", 0)

    return {
        "success": True,
        "input": {"vin": vin, "mileage": mileage},
        "vehicle_details": {
            "year": year,
            "make": make,
            "model": model,
            "trim": trim,
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
            "currency": valuation.get("currency"),
            "fair_price_range": {
                "low": round(estimated_price * 0.9, 2),
                "high": round(estimated_price * 1.1, 2),
            },
        },
        "metadata": {
            "valuation_method": valuation.get("method"),
            "source": "NHTSA + MarketCheck/Depreciation",
        },
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "API is running"}


@app.post("/analyze-document")
async def analyze_document(
    file: UploadFile = File(...),           # FIX 3: FastAPI uses UploadFile, not Flask's file_obj
    user_prompt: Optional[str] = None,
):
    """Analyze an uploaded document (image/PDF) with an optional user prompt."""
    temp_path = None
    try:
        # Determine file extension safely
        suffix = os.path.splitext(file.filename or "upload")[1] or ".tmp"

        # FIX 4: read bytes with await, then write — NOT file_obj.save()
        contents = await file.read()

        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        with open(temp_path, "wb") as f:
            f.write(contents)

        logger.info(f"Processing document: {file.filename}")

        # OCR extraction
        ocr_result = process_generic_file(temp_path)
        extracted_text = ocr_result.get("text", "")

        if not extracted_text:
            raise HTTPException(
                status_code=422,
                detail="Could not extract text from document. Ensure it's a clear image or PDF.",
            )

        # AI analysis
        analysis_result = negotiator.analyze_document_text(extracted_text, user_prompt)
        return analysis_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass


@app.post("/market-price")
def get_market_fair_price(request: MarketPriceRequest):
    """Return market fair price for a vehicle identified by VIN."""
    result = _build_market_price_response(request.vin, request.mileage)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result)
    return result


@app.post("/chat")
def chat_negotiation(request: ChatRequest):
    """Chat with the negotiation AI assistant."""
    response = negotiator.get_response(
        request.user_message, request.context, request.session_id
    )
    history = negotiator.get_chat_history(request.session_id)
    return {"success": True, "response": response, "history": history}


@app.get("/chat/history/{session_id}")
def get_chat_history(session_id: str = "default"):
    """Get the chat history for a session."""
    history = negotiator.get_chat_history(session_id)
    return {"success": True, "history": history}


@app.delete("/chat/history/{session_id}")
def clear_chat_history(session_id: str = "default"):
    """Clear the chat history for a session."""
    negotiator.clear_chat_history(session_id)
    return {"success": True, "message": "Chat history cleared"}
