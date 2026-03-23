import asyncio
import json
import re
import httpx
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from fastapi import HTTPException
from app.core.config import settings
from app.services.llm_logger import (
  log_llm_call, estimate_tokens, LLMCallTimer
)

# ─── VIN VALIDATION ────────────────────────────────────────
# Standard US VIN: exactly 17 alphanumeric chars
# Position 9 is check digit (0-9 or X)
# Positions 1-3: World Manufacturer Identifier
# US manufacturers start with: 1, 4, 5
# Indian manufacturers start with: MA, MB, MC, MD, ME, MZ
INDIAN_VIN_PREFIXES = ("MA", "MB", "MC", "MD", "ME", "MZ")

def is_valid_us_vin(vin: str) -> bool:
    """
    Returns True if VIN matches US NHTSA format.
    17 chars, alphanumeric, no I O Q characters.
    """
    if len(vin) != 17:
        return False
    if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin, re.IGNORECASE):
        return False
    return True

def is_indian_vin(vin: str) -> bool:
    """
    Returns True if VIN appears to be Indian format.
    Indian VINs start with MA-MZ (India country code).
    """
    return vin.upper().startswith(INDIAN_VIN_PREFIXES)

class VINService:
    NHTSA_DECODE = (
        "https://vpic.nhtsa.dot.gov/api/vehicles"
        "/decodevin/{vin}?format=json"
    )
    NHTSA_RECALLS = (
        "https://api.nhtsa.gov/recalls/recallsByVehicle"
    )
    NHTSA_COMPLAINTS = (
        "https://api.nhtsa.gov/complaints/complaintsByVehicle"
    )

    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            temperature=0,
            max_tokens=1000,
        )

    # ─── PUBLIC ENTRY POINT ──────────────────────────────────
    async def get_full_vin_report(
        self,
        vin: str,
        user_id=None,
        doc_id=None
    ) -> dict:
        """
        Main entry point for VIN lookup.

        Flow:
          1. Validate VIN format
          2. Check if Indian VIN -> return friendly message
          3. Decode VIN via NHTSA
          4. Fetch recalls + complaints concurrently
          5. Get market price estimate via Groq
          6. Build red flags
          7. Return full report
        """
        vin = vin.upper().strip()

        # Check Indian VIN first
        if is_indian_vin(vin):
            return {
                "vin": vin,
                "supported": False,
                "message": (
                    "This appears to be an Indian vehicle VIN. "
                    "NHTSA database only covers US market vehicles. "
                    "Please verify details with your dealer or RTO."
                ),
                "vehicle_info": None,
                "recalls": [],
                "complaints": {"total": 0, "top_components": []},
                "market_pricing": None,
                "red_flags": [],
            }

        # Validate US VIN format
        if not is_valid_us_vin(vin):
            return {
                "vin": vin,
                "supported": False,
                "message": (
                    f"VIN '{vin}' does not match standard format. "
                    "A valid VIN is 17 alphanumeric characters "
                    "(excluding I, O, Q). "
                    "Please check the VIN on your contract or vehicle."
                ),
                "vehicle_info": None,
                "recalls": [],
                "complaints": {"total": 0, "top_components": []},
                "market_pricing": None,
                "red_flags": [],
            }

        # Decode VIN
        vehicle_info = await self.decode_vin(vin)

        make  = vehicle_info.get("make", "")
        model = vehicle_info.get("model", "")
        year  = vehicle_info.get("year", "")
        trim  = vehicle_info.get("trim")

        # Fetch recalls + complaints concurrently
        # Do NOT include market pricing here — needs Groq delay
        recalls, complaints = await asyncio.gather(
            self.get_recalls(make, model, year),
            self.get_complaints(make, model, year),
        )

        # Delay before Groq call to respect rate limits
        await asyncio.sleep(2)

        # Get market pricing via Groq
        pricing = await self.get_market_price_estimate(
            make, model, year, trim,
            user_id=user_id,
            doc_id=doc_id
        )

        # Build red flags from recalls + complaints
        red_flags = []
        if len(recalls) > 0:
            red_flags.append(
                f"Vehicle has {len(recalls)} open recall(s) — "
                f"safety issue may exist"
            )
        if complaints["total"] > 50:
            red_flags.append(
                f"High complaint volume: {complaints['total']} "
                f"complaints filed with NHTSA"
            )
        if complaints["total"] > 200:
            red_flags.append(
                f"Very high complaint volume: {complaints['total']} "
                f"complaints — research this model carefully"
            )

        return {
            "vin": vin,
            "supported": True,
            "message": None,
            "vehicle_info": vehicle_info,
            "recalls": recalls,
            "complaints": complaints,
            "market_pricing": pricing,
            "red_flags": red_flags,
        }

    # ─── NHTSA DECODE ────────────────────────────────────────
    async def decode_vin(self, vin: str) -> dict:
        """
        Decode VIN using NHTSA free API.
        Returns clean dict of vehicle attributes.
        Raises HTTP 422 if VIN is invalid per NHTSA.
        """
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                self.NHTSA_DECODE.format(vin=vin)
            )
            resp.raise_for_status()

        field_map = {
            "Make": "make",
            "Model": "model",
            "Model Year": "year",
            "Trim": "trim",
            "Body Class": "body_class",
            "Displacement (L)": "engine_displacement",
            "Drive Type": "drive_type",
            "Fuel Type - Primary": "fuel_type",
            "Manufacturer Name": "manufacturer",
            "Vehicle Type": "vehicle_type",
            "Plant Country": "plant_country",
            "Series": "series",
        }

        result = {}
        for item in resp.json().get("Results", []):
            key = field_map.get(item.get("Variable", ""))
            value = item.get("Value", "")
            if key and value and value not in (
                "Not Applicable", "null", None, ""
            ):
                result[key] = value

        if not result.get("make"):
            raise HTTPException(
                422,
                f"NHTSA could not decode VIN: {vin}. "
                f"Please verify the VIN is correct."
            )

        return result

    # ─── RECALLS ─────────────────────────────────────────────
    async def get_recalls(
        self, make: str, model: str, year: str
    ) -> list:
        """
        Fetch safety recalls from NHTSA.
        Returns empty list if API fails — never raises.
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    self.NHTSA_RECALLS,
                    params={
                        "make": make,
                        "model": model,
                        "modelYear": year
                    }
                )
            if resp.status_code != 200:
                return []

            return [
                {
                    "component": r.get("Component", ""),
                    "recall_date": r.get("ReportReceivedDate", ""),
                    "summary": r.get("Summary", ""),
                    "consequence": r.get("Consequence", ""),
                    "remedy": r.get("Remedy", ""),
                    "campaign_number": r.get(
                        "NHTSACampaignNumber", ""
                    ),
                    "severity": self._assess_recall_severity(
                        r.get("Consequence", "")
                    ),
                }
                for r in resp.json().get("results", [])
            ]
        except Exception:
            return []

    def _assess_recall_severity(self, consequence: str) -> str:
        """
        Assess recall severity from consequence text.
        Returns: "HIGH", "MEDIUM", "LOW"
        """
        if not consequence:
            return "MEDIUM"
        consequence_lower = consequence.lower()
        if any(word in consequence_lower for word in [
            "crash", "fire", "death", "injury",
            "fatal", "burn", "rollover"
        ]):
            return "HIGH"
        elif any(word in consequence_lower for word in [
            "loss of control", "stall", "brake",
            "steering", "airbag"
        ]):
            return "MEDIUM"
        return "LOW"

    # ─── COMPLAINTS ──────────────────────────────────────────
    async def get_complaints(
        self, make: str, model: str, year: str
    ) -> dict:
        """
        Fetch owner complaints from NHTSA.
        Returns zero counts if API fails — never raises.
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    self.NHTSA_COMPLAINTS,
                    params={
                        "make": make,
                        "model": model,
                        "modelYear": year
                    }
                )
            if resp.status_code != 200:
                return {"total": 0, "top_components": []}

            results = resp.json().get("results", [])
            comp_count = {}
            for r in results:
                c = r.get("components", "Unknown")
                comp_count[c] = comp_count.get(c, 0) + 1

            top = sorted(
                comp_count,
                key=comp_count.get,
                reverse=True
            )[:5]

            return {
                "total": len(results),
                "top_components": [
                    {"component": c, "count": comp_count[c]}
                    for c in top
                ],
            }
        except Exception:
            return {"total": 0, "top_components": []}

    async def get_market_price_estimate(
        self,
        make: str,
        model: str,
        year: str,
        trim: str = None,
        user_id=None,
        doc_id=None
    ) -> dict:
        """
        Use Groq LLM to estimate market pricing.
        Caller must add 2 second delay before calling this.
        Returns pricing dict with honest AI disclaimer.
        Never raises — returns error dict if LLM fails.
        """
        trim_str = trim or ""
        prompt = f"""You are a US automotive pricing expert.
For a {year} {make} {model} {trim_str} in average condition
in the US market, provide realistic current price ranges.

Return ONLY this exact JSON structure.
No explanation. No markdown. Start with {{ end with }}

{{
  "private_party_low": "$XX,XXX",
  "private_party_high": "$XX,XXX",
  "dealer_retail_low": "$XX,XXX",
  "dealer_retail_high": "$XX,XXX",
  "fair_monthly_lease_low": "$XXX",
  "fair_monthly_lease_high": "$XXX",
  "fair_monthly_loan_low": "$XXX",
  "fair_monthly_loan_high": "$XXX",
  "msrp_estimate": "$XX,XXX",
  "data_note": "AI-based estimate — verify with official sources before making financial decisions"
}}"""

        timer = LLMCallTimer()
        prompt_tokens = estimate_tokens(prompt)

        try:
            timer.start()
            response = await self.llm.ainvoke(
                [HumanMessage(content=prompt)]
            )
            elapsed = timer.stop()

            completion_tokens = estimate_tokens(
                response.content
            )

            import asyncio
            asyncio.create_task(log_llm_call(
                module="vin_pricing",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                response_time_ms=elapsed,
                success=True,
                user_id=user_id,
                doc_id=doc_id,
            ))
            raw = re.sub(
                r"```json|```", "", response.content
            ).strip()

            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not json_match:
                return self._pricing_unavailable()

            return json.loads(json_match.group())

        except Exception:
            asyncio.create_task(log_llm_call(
                module="vin_pricing",
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                response_time_ms=timer.stop(),
                success=False,
                error_message="Pricing LLM failed",
                user_id=user_id,
                doc_id=doc_id,
            ))
            return self._pricing_unavailable()

    def _pricing_unavailable(self) -> dict:
        return {
            "data_note": (
                "Pricing estimate unavailable. "
                "Please check Edmunds, KBB, or CarGurus "
                "for current market prices."
            )
        }

# Singleton instance
vin_service = VINService()
