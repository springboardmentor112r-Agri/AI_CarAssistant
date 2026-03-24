import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -----------------------------
# Helper: extract vehicle info from text
# -----------------------------
def extract_vehicle_info_from_text(text: str):
    vin = re.search(r"VIN[:\s]*([A-HJ-NPR-Z0-9]{17})", text, re.I)
    make = re.search(r"Make[:\s]*([\w\-]+)", text, re.I)
    model = re.search(r"Model[:\s]*([\w\s\-]+)", text, re.I)
    year = re.search(r"(?:Model Year|Year)[:\s]*(\d{4})", text, re.I)
    trim = re.search(r"Trim[:\s]*([\w\s\-]+)", text, re.I)
    
    return {
        "vin": vin.group(1) if vin else None,
        "make": make.group(1) if make else None,
        "model": model.group(1) if model else None,
        "year": int(year.group(1)) if year else None,
        "trim": trim.group(1) if trim else None
    }

# -----------------------------
# Main SLA / Contract extraction
# -----------------------------
def extract_sla(contract_text: str) -> dict:
    # Pre-extract vehicle info using regex
    pre_extracted_vehicle = extract_vehicle_info_from_text(contract_text)

    # LLM prompt
    prompt = f"""
You are a contract analysis engine.

Extract the following data from the contract.

Return ONLY valid JSON.

{{
  "vehicle_info": {{
    "vin": null,
    "make": null,
    "model": null,
    "year": null,
    "trim": null
  }},
  "financial_terms": {{
    "interest_rate_apr": null,
    "lease_term_months": null,
    "monthly_payment": null,
    "down_payment": null,
    "residual_value": null,
    "purchase_option_buyout_price": null
  }},
  "usage_terms": {{
    "mileage_allowance": null,
    "overage_charges": null
  }},
  "contract_conditions": {{
    "early_termination_clause": null,
    "maintenance_responsibilities": null,
    "warranty_and_insurance": null,
    "penalties_or_late_fees": null
  }}
}}

Contract:
<<<{contract_text}>>>
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a strict JSON extraction engine. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    raw_output = response.choices[0].message.content.strip()
    raw_output = raw_output.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw_output)

        # Merge regex vehicle info with LLM output
        vehicle_info = parsed.get("vehicle_info", {})
        for key, value in pre_extracted_vehicle.items():
            if value is not None:
                vehicle_info[key] = value

        # Risk analysis
        contract_conditions = parsed.get("contract_conditions", {})
        red_flags = []

        early_term = contract_conditions.get("early_termination_clause")
        if early_term and isinstance(early_term, dict) and early_term.get("fee", 0) > 0:
            red_flags.append("High early termination fee")

        penalties = contract_conditions.get("penalties_or_late_fees")
        if penalties and isinstance(penalties, dict) and (
            penalties.get("late_payment_fee", 0) > 0 or penalties.get("additional_interest", 0) > 0
        ):
            red_flags.append("Late payment penalties or interest charges")

        insurance = contract_conditions.get("warranty_and_insurance")
        if insurance and isinstance(insurance, dict) and insurance.get("insurance_requirements"):
            red_flags.append("Strict insurance requirements")

        # fairness_score = max(100 - len(red_flags) * 20, 0)

        structured_output = {
            "Vehicle Info": vehicle_info,
            "Financial Terms": parsed.get("financial_terms", {}),
            "Usage Terms": parsed.get("usage_terms", {}),
            "Contract Conditions": contract_conditions
            # "Risk Analysis": {
            #     "red_flags": red_flags,
            #     "contract_fairness_score": fairness_score
            # }
        }

        return structured_output

    except json.JSONDecodeError:
        return {"error": "Invalid JSON returned by LLM", "raw_output": raw_output}


# -----------------------------------
# AI Contract Assistant
# -----------------------------------

def contract_ai_assistant(contract_text: str, user_question: str):
    
    prompt = f"""
You are an AI assistant helping a user understand a car lease or loan contract.

INSTRUCTIONS:
- Answer ONLY using information from the contract provided below
- Keep your answer to 3-4 lines maximum
- Be concise and direct - no introductory phrases or conclusions
- Use simple, plain language that anyone can understand
- Structure your answer to directly address the user's question
- If information is not in the contract, simply say: "This information is not present in the contract."

CONTRACT:
<<<{contract_text}>>>

USER QUESTION:
{user_question}

YOUR ANSWER (3-4 lines max):
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful contract assistant. You provide concise, accurate answers in 3-4 lines maximum using only contract information."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1  # Lower temperature for more consistent, factual responses
    )

    answer = response.choices[0].message.content.strip()
    
    # Ensure answer isn't too long (rough check)
    if len(answer.split('\n')) > 4 or len(answer.split('.')) > 4:
        # If too long, take first 3 sentences
        sentences = answer.split('.')
        answer = '. '.join(sentences[:3]) + '.'
    
    return answer



















# import re

# def simple_sla_extraction(contract_text):
#     data = {}

#     # APR
#     apr_match = re.search(r'(APR|Annual Percentage Rate).*?([\d.]+)\s*%', contract_text, re.IGNORECASE)
#     if apr_match:
#         data["apr"] = float(apr_match.group(2))

#     # Term (months)
#     term_match = re.search(r'(term|period).*?(\d+)\s*months', contract_text, re.IGNORECASE)
#     if term_match:
#         data["term_months"] = int(term_match.group(2))

#     # Monthly payment
#     payment_match = re.search(r'(monthly).*?(payment).*?([\$USD₹]?\s*[\d,]+)', contract_text, re.IGNORECASE)
#     if payment_match:
#         data["monthly_payment"] = payment_match.group(3)

#     # Down payment
#     down_match = re.search(r'(down).*?(payment).*?([\$USD₹]?\s*[\d,]+)', contract_text, re.IGNORECASE)
#     if down_match:
#         data["down_payment"] = down_match.group(3)

#     # Mileage
#     mileage_match = re.search(r'(mileage|km|kilometers).*?([\d,]+)', contract_text, re.IGNORECASE)
#     if mileage_match:
#         data["mileage_per_year"] = mileage_match.group(2)

#     return data







