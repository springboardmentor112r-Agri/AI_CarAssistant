from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_contract(text: str) -> str:
    prompt = f"""You are an expert analyst of automotive finance contracts (car leases and loans — especially BMW Financial Services style documents).

Extract key values **strictly** in this JSON format. Return **ONLY** valid JSON — no explanations, no markdown, no extra text.

{{
  "contract_type": "lease|loan|hire_purchase|other",
  "vehicle": "",
  "lease_term_months": "",
  "monthly_installment": "",
  "initial_payment_or_downpayment": "",
  "amount_due_at_signing": "",
  "capitalized_cost_reduction": "",
  "residual_value": "",
  "money_factor": "",
  "annual_mileage_limit": "",
  "excess_mileage_charge": "",
  "interest_rate_or_apr_percent": "",
  "buyout_price_end_of_term": "",
  "early_termination_fee": "",
  "disposition_fee": "",
  "maintenance_responsibility": "",
  "important_warnings": []   // array of short strings — red flags, unusual clauses, etc.
}}

Contract text (use clearest matches — be conservative — empty string if not found):
{text[:11000]}

Rules:
- Use exact values and units as written (e.g. "15,000 km/year", "4.99%", "₹5,99,999").
- If value is a range or description → keep short & accurate.
- "important_warnings": list anything unusual, risky or consumer-unfriendly.
- Output **only** valid JSON.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # fast & free-tier friendly; change to "llama-3.3-70b-versatile" for better quality if limits allow
            messages=[
                {"role": "system", "content": "You are a precise legal-term extractor. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,          # low for deterministic JSON
            max_tokens=800,
            stream=False
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except Exception as e:
        return json.dumps({
            "error": "Groq API call failed",
            "detail": str(e)
        })