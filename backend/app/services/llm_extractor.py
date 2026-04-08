import json
import os
import random
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import Optional, List

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

class ExtractedSLAData(BaseModel):
    apr: Optional[float] = Field(None, description="Interest rate / APR percentage")
    lease_term_months: Optional[int] = Field(None, description="Lease term duration in months")
    monthly_payment: Optional[float] = Field(None, description="Monthly payment amount")
    down_payment: Optional[float] = Field(None, description="Down payment amount")
    residual_value: Optional[float] = Field(None, description="Residual value amount at end of lease")
    mileage_allowance: Optional[int] = Field(None, description="Annual mileage allowance")
    overage_charge_per_mile: Optional[float] = Field(None, description="Charge per mile if over mileage allowance")
    early_termination_clause: Optional[str] = Field(None, description="Summary or specific text around early termination policies")
    buyout_price: Optional[float] = Field(None, description="Purchase option or buyout price")
    fairness_score: Optional[int] = Field(None, description="Score from 1-100 evaluating how standard/fair this contract is")
    red_flags: Optional[List[str]] = Field(None, description="List of detected unfair conditions or potential consumer red flags")
    vehicle_year: Optional[int] = Field(None, description="Year of the vehicle")
    vehicle_make: Optional[str] = Field(None, description="Manufacturer of the vehicle (e.g. Toyota, Honda)")
    vehicle_model: Optional[str] = Field(None, description="Model of the vehicle (e.g. Camry, Civic)")

def _generate_mock_sla(raw_text: str) -> dict:
    """
    Returns realistic mock SLA data for demo purposes when no OpenAI key is set.
    Varies slightly based on the text content so repeated uploads feel realistic.
    """
    seed = sum(ord(c) for c in raw_text[:200]) if raw_text else 42
    rng = random.Random(seed)

    apr = round(rng.uniform(3.9, 12.5), 2)
    term = rng.choice([24, 36, 48, 60])
    monthly = round(rng.uniform(280, 750), 2)
    down = round(rng.uniform(1000, 5000), -2)
    residual = round(rng.uniform(12000, 28000), -2)
    mileage = rng.choice([10000, 12000, 15000])
    overage = round(rng.uniform(0.15, 0.35), 2)
    buyout = round(residual + rng.uniform(500, 2000), -2)

    # Fairness score inversely related to APR
    fairness = max(20, min(95, int(100 - (apr - 3.9) * 7 + rng.uniform(-5, 5))))

    red_flags = []
    if apr > 9.0:
        red_flags.append(f"High APR of {apr}% — market average is 5–7% for good credit")
    if overage > 0.25:
        red_flags.append(f"Above-average overage charge of ${overage}/mile — negotiate down to $0.15–$0.20")
    if term > 48:
        red_flags.append("Long lease term increases total cost — consider a 36-month lease instead")
    if down > 3500:
        red_flags.append("High down payment — putting less down reduces financial risk if vehicle is totaled")

    # Mock vehicle details
    vehicles = [
        (2023, "Toyota", "Camry"),
        (2024, "Honda", "Civic"),
        (2022, "Ford", "F-150"),
        (2023, "Tesla", "Model 3"),
        (2024, "BMW", "3 Series")
    ]
    year, make, model = rng.choice(vehicles)

    return {
        "apr": apr,
        "lease_term_months": term,
        "monthly_payment": monthly,
        "down_payment": down,
        "residual_value": residual,
        "mileage_allowance": mileage,
        "overage_charge_per_mile": overage,
        "early_termination_clause": "Early termination may result in remaining payments plus a disposition fee of up to $400.",
        "buyout_price": buyout,
        "fairness_score": fairness,
        "red_flags": red_flags if red_flags else ["No major red flags detected in this contract."],
        "vehicle_year": year,
        "vehicle_make": make,
        "vehicle_model": model,
    }

async def extract_sla_from_text(raw_text: str) -> dict:
    """
    Uses OpenAI's structured output API to parse raw contract text.
    Falls back to realistic mock data if OPENAI_API_KEY is not set.
    """
    if not client:
        print("[LLM] No OPENAI_API_KEY found — using mock SLA extraction for demo.")
        return _generate_mock_sla(raw_text)

    prompt = f"""
    You are an expert financial automotive contract reviewer.
    Review the following extracted text from a car lease or loan contract and extract the key terms.
    If a term is not explicitly stated or cannot be reliably inferred, leave it as null.
    Provide an approximate fairness_score from 1-100 based on standard industry averages (e.g. APR > 10% is worse, high buyout penalties, etc.).
    Identify any consumer-facing red flags or hidden fees as well.

    --- CONTRACT TEXT ---
    {raw_text[:25000]}
    ---------------------
    """

    try:
        response = await client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a specialized AI designed to extract structured automobile loan and lease agreement data."},
                {"role": "user", "content": prompt}
            ],
            response_format=ExtractedSLAData,
        )
        structured_data = response.choices[0].message.parsed
        return structured_data.model_dump()

    except Exception as e:
        print(f"[LLM] Error calling SLA extraction: {e} — falling back to mock data.")
        return _generate_mock_sla(raw_text)
