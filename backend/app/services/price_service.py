import httpx
from typing import Optional, Dict


async def estimate_price(make: str, model: str, year: int, postal_code: str = "") -> Dict:
    """
    Estimate fair market price using NHTSA + basic heuristics.
    In production, replace with Edmunds or TrueCar API.
    """
    # NHTSA gives base specs; we'll build heuristic pricing
    base_prices = {
        "toyota": {"camry": 26000, "corolla": 22000, "rav4": 30000, "highlander": 38000},
        "honda": {"accord": 28000, "civic": 24000, "cr-v": 31000, "pilot": 40000},
        "ford": {"f-150": 38000, "mustang": 30000, "escape": 28000, "explorer": 36000},
        "chevrolet": {"malibu": 24000, "silverado": 38000, "equinox": 28000},
        "bmw": {"3 series": 44000, "5 series": 56000, "x3": 48000, "x5": 62000},
        "mercedes-benz": {"c-class": 46000, "e-class": 58000, "glc": 50000},
        "tesla": {"model 3": 45000, "model y": 52000, "model s": 90000},
    }

    make_lower = make.lower()
    model_lower = model.lower()

    base = base_prices.get(make_lower, {}).get(model_lower, 30000)

    # Age depreciation (~12% per year)
    current_year = 2025
    age = current_year - year
    depreciation = (1 - 0.12) ** age
    estimated_value = base * depreciation

    return {
        "msrp": round(base, 2),
        "fair_price_low": round(estimated_value * 0.92, 2),
        "fair_price_high": round(estimated_value * 1.03, 2),
        "basis": f"Heuristic estimate for {year} {make} {model}",
        "methodology": (
            "Base MSRP from internal lookup + 12% annual depreciation model. "
            "For production, integrate Edmunds or TrueCar API for real-time market data."
        ),
        "geo_postal": postal_code,
    }