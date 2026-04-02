import os, json
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-20250514"

SYSTEM_NEGOTIATION = """You are AutoGuard, an expert AI assistant specializing in car lease and loan contracts.
You help users understand their contracts, identify unfair terms, and negotiate better deals.
Be concise, practical, and use bullet points where helpful. Focus on actionable advice."""


def extract_sla_with_llm(contract_text: str) -> dict:
    """Use Claude to extract SLA fields from contract text."""
    prompt = f"""Extract the following fields from this car lease/loan contract text.
Return ONLY a valid JSON object with these exact keys (use null if not found):

{{
  "apr": <number or null>,
  "term_months": <integer or null>,
  "monthly_payment": <number or null>,
  "down_payment": <number or null>,
  "mileage_allowance": <integer per year or null>,
  "mileage_overage_fee": <number per mile or null>,
  "residual_value": <percentage number or null>,
  "early_termination": <dollar amount or null>,
  "buyout_price": <dollar amount or null>,
  "warranty_summary": <short string or null>
}}

CONTRACT TEXT:
{contract_text[:6000]}

Return ONLY the JSON object, no explanation, no markdown."""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    # Strip markdown fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def compute_fairness_score(sla: dict) -> float:
    """Score the contract 0-100 based on market benchmarks."""
    score = 100.0
    deductions = []

    apr = sla.get("apr")
    if apr:
        if apr > 8:
            deductions.append(20)
        elif apr > 6:
            deductions.append(12)
        elif apr > 4.5:
            deductions.append(5)

    overage = sla.get("mileage_overage_fee")
    if overage:
        if overage > 0.22:
            deductions.append(15)
        elif overage > 0.18:
            deductions.append(8)

    early = sla.get("early_termination")
    if early:
        if early > 2000:
            deductions.append(15)
        elif early > 1200:
            deductions.append(8)

    down = sla.get("down_payment")
    if down:
        monthly = sla.get("monthly_payment") or 500
        if down > monthly * 5:
            deductions.append(10)

    score -= sum(deductions)
    return max(0.0, round(score, 1))


def generate_flags(sla: dict) -> list:
    """Generate red/yellow/green flags based on SLA values."""
    flags = []

    apr = sla.get("apr")
    if apr:
        if apr > 7:
            flags.append({"severity": "red", "message": f"APR {apr}% — Market average is ~5%. You may overpay significantly."})
        elif apr > 5.5:
            flags.append({"severity": "yellow", "message": f"APR {apr}% — Slightly above market. Try negotiating down."})
        else:
            flags.append({"severity": "green", "message": f"APR {apr}% — Competitive rate."})

    overage = sla.get("mileage_overage_fee")
    if overage:
        if overage > 0.22:
            flags.append({"severity": "red", "message": f"Mileage overage ${overage}/mile — Standard is $0.15–$0.20. Request reduction."})
        elif overage > 0.18:
            flags.append({"severity": "yellow", "message": f"Mileage overage ${overage}/mile — Slightly high. Negotiable."})

    early = sla.get("early_termination")
    if early:
        if early > 2000:
            flags.append({"severity": "red", "message": f"Early termination fee ${early} — High. Negotiate cap to $800–$1,200."})
        elif early > 1000:
            flags.append({"severity": "yellow", "message": f"Early termination fee ${early} — Slightly above average."})

    residual = sla.get("residual_value")
    if residual:
        if 48 <= residual <= 58:
            flags.append({"severity": "green", "message": f"Residual value {residual}% — In line with market benchmarks."})
        elif residual < 45:
            flags.append({"severity": "yellow", "message": f"Residual value {residual}% — Lower than average, monthly payments may be higher."})

    down = sla.get("down_payment")
    if down and down > 3000:
        flags.append({"severity": "yellow", "message": f"Down payment ${down} — Consider negotiating lower to preserve cash."})

    return flags


def get_negotiation_response(user_message: str, history: list, sla_context: str) -> str:
    """Get AI response for the negotiation chatbot."""
    system = SYSTEM_NEGOTIATION
    if sla_context:
        system += f"\n\nCurrent contract context: {sla_context}"

    messages = history + [{"role": "user", "content": user_message}]

    resp = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system,
        messages=messages,
    )
    return resp.content[0].text
