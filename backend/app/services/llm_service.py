import json
import re
import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

EXTRACTION_PROMPT = """
You are an expert automotive finance contract analyst. Analyze the following car lease or loan contract text and extract ALL key SLA fields.

Return ONLY valid JSON with no extra text, no markdown, no backticks. Use null for missing values.

Required JSON structure:
{{
  "contract_type": "lease" or "loan",
  "dealer_offer_name": "string or null",
  "contract_date": "string or null",
  "apr_percent": number or null,
  "money_factor": number or null,
  "term_months": integer or null,
  "monthly_payment": number or null,
  "down_payment": number or null,
  "fees_total": number or null,
  "residual_value": number or null,
  "residual_percent_msrp": number or null,
  "msrp": number or null,
  "cap_cost": number or null,
  "cap_cost_reduction": number or null,
  "mileage_allowance_yr": integer or null,
  "mileage_overage_fee": number or null,
  "early_termination_fee": number or null,
  "disposition_fee": number or null,
  "purchase_option_price": number or null,
  "insurance_requirements": "string or null",
  "maintenance_resp": "string or null",
  "warranty_summary": "string or null",
  "late_fee_policy": "string or null",
  "vehicle_vin": "string or null",
  "vehicle_year": integer or null,
  "vehicle_make": "string or null",
  "vehicle_model": "string or null",
  "vehicle_trim": "string or null",
  "red_flags": ["list of concerning clauses as strings"],
  "negotiation_points": ["list of specific negotiation suggestions as strings"],
  "fairness_score": number between 0-100,
  "fairness_explanation": "string",
  "plain_summary": "A simple 3-4 sentence plain English summary of this contract that anyone can understand. Include the most important numbers and whether this is a good or bad deal."
}}

Contract Text:
{contract_text}
"""

NEGOTIATION_PROMPT = """
You are an expert car lease and loan negotiation coach.
The user is negotiating a car deal and needs your help.

Contract Context:
{contract_context}

User Message: {user_message}

IMPORTANT FORMATTING RULES:
- Always give answers in clear bullet points
- Use simple everyday language — no complex financial jargon
- Break down numbers clearly
- Use emojis to make it friendly and easy to read
- Make every point short and clear — one idea per point
- If there are calculations show them step by step
- End with a simple conclusion
- ALWAYS return response as a single string, never as a list or array

Format your response as JSON:
{{
  "response": "your pointwise friendly response with emojis and clear formatting as a single string",
  "suggested_dealer_message": "ready-to-send professional message for the dealer as a single string"
}}

Example response format:
💰 Total Payment Breakdown:
- Down Payment: $12,000
- Monthly Payment: $1,450 x 24 months = $34,800
- Total Amount: $46,800

⚠️ Things to Watch Out For:
- Early termination fee is high at $6,000
- Mileage limit is only 6,000/year — very low

✅ Bottom Line:
- This deal is average — you can negotiate better terms
"""

COMPARISON_PROMPT = """
You are an automotive finance expert. Compare these two car deals and give a clear recommendation.

Deal 1 (Primary):
{deal1}

Deal 2 (Comparison):
{deal2}

IMPORTANT FORMATTING RULES:
- Give answers in clear bullet points
- Use simple everyday language
- Use emojis to make it friendly
- Show clear winner with reasons
- ALWAYS return analysis as a single string, never as a list or array

Return ONLY valid JSON:
{{
  "winner": "deal1" or "deal2" or "tie",
  "analysis": "detailed pointwise comparison with emojis and bullet points as a single string",
  "savings": number,
  "key_differences": ["list of key differences as strings"]
}}
"""


def extract_sla_from_text(contract_text: str) -> dict:
    """Use Gemini to extract SLA fields from contract text."""
    prompt = EXTRACTION_PROMPT.format(contract_text=contract_text[:8000])
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=8192,
        )
    )
    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            last_comma = raw.rfind(',')
            if last_comma > 0:
                fixed = raw[:last_comma] + '\n}'
                return json.loads(fixed)
        except Exception:
            pass

        return {
            "contract_type": "lease",
            "apr_percent": None,
            "term_months": None,
            "monthly_payment": None,
            "down_payment": None,
            "fees_total": None,
            "residual_value": None,
            "msrp": None,
            "cap_cost": None,
            "mileage_allowance_yr": None,
            "mileage_overage_fee": None,
            "early_termination_fee": None,
            "vehicle_vin": None,
            "vehicle_year": None,
            "vehicle_make": None,
            "vehicle_model": None,
            "red_flags": ["Could not fully parse contract — please re-upload"],
            "negotiation_points": [],
            "fairness_score": 50,
            "fairness_explanation": "Could not fully analyze contract",
            "plain_summary": "Contract could not be fully analyzed. Please try re-uploading."
        }


def get_negotiation_response(contract_context: str, user_message: str) -> dict:
    """Generate negotiation advice and dealer message using Gemini."""
    prompt = NEGOTIATION_PROMPT.format(
        contract_context=contract_context[:4000],
        user_message=user_message,
    )
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=4096,
        )
    )
    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        result = json.loads(raw)
        # Make sure response is always a string not a list
        if isinstance(result.get("response"), list):
            result["response"] = "\n".join(result["response"])
        if isinstance(result.get("suggested_dealer_message"), list):
            result["suggested_dealer_message"] = "\n".join(result["suggested_dealer_message"])
        return result
    except json.JSONDecodeError:
        return {"response": raw, "suggested_dealer_message": ""}


def compare_deals(deal1: dict, deal2: dict) -> dict:
    """Compare two contract SLAs and return analysis."""
    prompt = COMPARISON_PROMPT.format(
        deal1=json.dumps(deal1, indent=2),
        deal2=json.dumps(deal2, indent=2),
    )
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=4096,
        )
    )
    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        result = json.loads(raw)
        # Make sure analysis is always a string not a list
        if isinstance(result.get("analysis"), list):
            result["analysis"] = "\n".join(result["analysis"])
        return result
    except json.JSONDecodeError:
        return {"winner": "unknown", "analysis": raw, "savings": 0, "key_differences": []}