import httpx
from typing import Optional, Dict, List
from app.core.config import settings

NHTSA_DECODE_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"
NHTSA_RECALLS_URL = "https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}"


async def decode_vin(vin: str) -> Optional[Dict]:
    """Decode a VIN using NHTSA public API."""
    url = NHTSA_DECODE_URL.format(vin=vin.strip().upper())
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("Results", [])
    if not results:
        return None

    r = results[0]

    def safe(key):
        val = r.get(key, "")
        return val if val else None

    return {
        "vin": vin.upper(),
        "year": int(safe("ModelYear")) if safe("ModelYear") else None,
        "make": safe("Make"),
        "model": safe("Model"),
        "trim": safe("Trim"),
        "body_class": safe("BodyClass"),
        "engine": safe("DisplacementL"),
        "drivetrain": safe("DriveType"),
        "fuel_type": safe("FuelTypePrimary"),
        "plant_country": safe("PlantCountry"),
        "series": safe("Series"),
    }


async def get_recalls(make: str, model: str, year: int) -> List[Dict]:
    """Fetch recall data from NHTSA for a specific vehicle."""
    url = NHTSA_RECALLS_URL.format(
        make=make.strip(),
        model=model.strip(),
        year=year,
    )
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

    recalls = []
    for item in data.get("results", []):
        recalls.append({
            "recall_number": item.get("NHTSACampaignNumber"),
            "issue_date": item.get("ReportReceivedDate"),
            "component": item.get("Component"),
            "summary": item.get("Summary"),
            "remedy": item.get("Remedy"),
            "source": "NHTSA",
            "raw": item,
        })
    return recalls