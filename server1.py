"""
DealSense AI - Unified Flask Server
Combines VIN Decode, Valuation, Chatbot, Document Analysis, and Auth.
"""

import os
import json
import re
import secrets
import logging
import tempfile

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Gemini setup ──────────────────────────────────────────────────────────────
GEMINI_AVAILABLE = False
gemini_client = None
try:
    from google import genai
    _key = os.getenv("GEMINI_API_KEY")
    if _key:
        gemini_client = genai.Client(api_key=_key)
        GEMINI_AVAILABLE = True
        logger.info("✅ Gemini AI initialized")
except ImportError:
    logger.warning("⚠️ google-genai not installed")

# ── Groq setup ────────────────────────────────────────────────────────────────
GROQ_AVAILABLE = False
groq_client = None
try:
    from groq import Groq
    _groq_key = os.getenv("GROQ_API_KEY")
    if _groq_key:
        groq_client = Groq(api_key=_groq_key)
        GROQ_AVAILABLE = True
        logger.info("✅ Groq AI initialized")
except ImportError:
    logger.warning("⚠️ groq not installed")

# ── Local imports ─────────────────────────────────────────────────────────────
from backend.app.vin_decoder import decode_vin_nhtsa
from backend.app.valuation import estimate_fair_price, get_vin_insights
from backend.app.ocr import process_generic_file
from backend.app.negotiation import NegotiationEngine

# ── Flask App ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# ── Global negotiator ─────────────────────────────────────────────────────────
negotiator = NegotiationEngine()

# ── Auth store ────────────────────────────────────────────────────────────────
USERS = {
    "admin": "admin123",
    "demo":  "demo123",
}
active_tokens = {}   # token -> username


# ── Auth helper ───────────────────────────────────────────────────────────────
def get_token_user():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return active_tokens.get(auth.split(" ")[1])
    return None


# ── AI helper ─────────────────────────────────────────────────────────────────
def call_ai(prompt: str, max_tokens: int = 1000) -> str | None:
    """Try Groq first, fallback to Gemini."""
    # Groq (faster, generous free tier)
    if GROQ_AVAILABLE and groq_client:
        try:
            r = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Groq failed: {e}")

    # Gemini fallback
    if GEMINI_AVAILABLE and gemini_client:
        try:
            r = gemini_client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
            )
            return r.text.strip() if r and r.text else None
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")

    return None


# ─────────────────────────────────────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')

    expected = USERS.get(username)
    if not expected or expected != password:
        return jsonify({"success": False, "error": "Incorrect username or password."})

    token = secrets.token_hex(32)
    active_tokens[token] = username
    logger.info(f"✅ User '{username}' logged in")
    return jsonify({"success": True, "token": token, "username": username})


@app.route('/api/logout', methods=['POST'])
def logout():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ")[1]
        user = active_tokens.pop(token, None)
        if user:
            logger.info(f"User '{user}' logged out")
    return jsonify({"success": True, "message": "Logged out"})


@app.route('/api/verify', methods=['GET'])
def verify():
    username = get_token_user()
    if not username:
        return jsonify({"success": False, "error": "Invalid or expired token"})
    return jsonify({"success": True, "username": username})


# ─────────────────────────────────────────────────────────────────────────────
# MARKET VALUE
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/market_value', methods=['GET', 'POST'])
def market_value_endpoint():
    if request.method == 'POST':
        data = request.get_json() or {}
        vin = data.get('vin', '')
        mileage = data.get('mileage', 12000)
    else:
        vin = request.args.get('vin', '')
        mileage = int(request.args.get('mileage', 12000))

    if not vin:
        return jsonify({"success": False, "error": "VIN is required"}), 400

    decoded = decode_vin_nhtsa(vin)
    if not decoded.get("success"):
        return jsonify({"success": False, "error": f"VIN Decode Failed: {decoded.get('error')}"})

    year  = decoded.get("year")
    make  = decoded.get("make")
    model = decoded.get("model")
    trim  = decoded.get("trim")

    if not all([year, make, model]):
        return jsonify({"success": False, "error": "Could not extract Year/Make/Model from VIN."})

    valuation = estimate_fair_price(year, make, model, mileage, vin=vin)
    if not valuation.get("success"):
        return jsonify({"success": False, "error": f"Valuation Failed: {valuation.get('error')}"})

    estimated_price = valuation.get("estimated_price", 0) or 0

    return jsonify({
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
    })


# ─────────────────────────────────────────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    data = request.get_json() or {}
    message    = data.get('message', '')
    context    = data.get('context', {})
    session_id = data.get('session_id', 'default')

    if not message:
        return jsonify({"success": False, "error": "Message is required"}), 400

    response = negotiator.get_response(message, context, session_id)
    history  = negotiator.get_chat_history(session_id)
    return jsonify({"success": True, "response": response, "history": history})


@app.route('/api/chat/history', methods=['GET'])
def chat_history_endpoint():
    session_id = request.args.get('session_id', 'default')
    history = negotiator.get_chat_history(session_id)
    return jsonify({"success": True, "history": history})


@app.route('/api/chat/clear', methods=['POST'])
def chat_clear_endpoint():
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    negotiator.clear_chat_history(session_id)
    return jsonify({"success": True, "message": "Chat history cleared"})


# ─────────────────────────────────────────────────────────────────────────────
# VIN INSIGHTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/vin_insights', methods=['GET'])
def vin_insights_endpoint():
    vin = request.args.get('vin', '')
    if not vin:
        return jsonify({"success": False, "error": "VIN is required"}), 400

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

        raw = call_ai(prompt, max_tokens=300)

        if raw:
            raw = re.sub(r"^```(?:json)?", "", raw).strip()
            raw = re.sub(r"```$", "", raw).strip()
            insights = json.loads(raw)
            return jsonify({
                "success": True,
                "days_on_market":   insights.get("days_on_market"),
                "market_position":  insights.get("market_position"),
                "negotiation_tips": insights.get("negotiation_tips", []),
            })

    except Exception as e:
        logger.error(f"VIN insights failed: {e}")

    # Safe fallback
    return jsonify({
        "success": True,
        "days_on_market": None,
        "market_position": None,
        "negotiation_tips": [
            "Ask the dealer for their best out-the-door price first.",
            "Research competing listings to use as leverage.",
            "Negotiate the total price, not just the monthly payment.",
        ],
    })


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/document/analyze', methods=['POST'])
def analyze_document_endpoint():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400

    user_prompt = request.form.get('prompt', None)
    temp_path = None

    try:
        suffix = os.path.splitext(file.filename)[1] or ".tmp"
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        file.save(temp_path)

        logger.info(f"Analyzing: {file.filename} | prompt: {user_prompt}")

        # Step 1: pdfplumber for digital PDFs
        extracted_text = ""
        try:
            import pdfplumber
            with pdfplumber.open(temp_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
            logger.info(f"pdfplumber: {len(extracted_text)} chars")
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")

        # Step 2: OCR fallback
        if not extracted_text.strip():
            ocr_result = process_generic_file(temp_path)
            extracted_text = ocr_result.get("text", "").strip()
            logger.info(f"OCR: {len(extracted_text)} chars")

        if not extracted_text.strip():
            return jsonify({
                "success": False,
                "error": "Could not extract text. Please upload a clearer image or PDF.",
            })

        # Step 3: AI analysis
        question = user_prompt or "Extract and summarize all key information from this car document."
        ai_prompt = f"""You are a car negotiation expert analyzing a dealer document.

USER QUESTION: {question}

DOCUMENT TEXT:
{extracted_text[:4000]}

Tasks:
- Identify document type (window sticker, buyer's order, invoice, etc.)
- Extract: VIN, Year, Make, Model, Trim, Price, Fees, Add-ons
- Flag any hidden fees, dealer markups, or red flags
- Give specific negotiation advice based on the document"""

        response_text = call_ai(ai_prompt, max_tokens=1000)

        if response_text:
            return jsonify({
                "success": True,
                "response": response_text,
                "is_conversation": True,
            })

        return jsonify({
            "success": False,
            "error": "AI service unavailable. Please try again later.",
        })

    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        return jsonify({"success": False, "error": str(e)})
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# SERVE FRONTEND
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def serve_frontend():
    return send_from_directory('frontend', 'login.html')   # Show login first

@app.route('/app')
def serve_app():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)


# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🚗  DealSense AI - Unified Server")
    print("=" * 50)
    print(f"\n📍 Open: http://localhost:5000")
    print(f"🤖 Groq  available: {GROQ_AVAILABLE}")
    print(f"🤖 Gemini available: {GEMINI_AVAILABLE}")
    print("\n📡 API Endpoints:")
    print("   POST /api/login              - Login")
    print("   POST /api/logout             - Logout")
    print("   GET  /api/verify             - Verify token")
    print("   GET  /api/market_value?vin=  - Get car value")
    print("   POST /api/chat               - Chat with AI")
    print("   GET  /api/chat/history       - Get chat history")
    print("   GET  /api/vin_insights?vin=  - Get insights")
    print("   POST /api/document/analyze   - Analyze document")
    print("\n🔑 Demo login: admin / admin123")
    print("=" * 50 + "\n")

    app.run(debug=True, port=5000)
