import requests
from typing import Dict, Any, Optional

VIN_API = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues"
RECALL_API = "https://api.nhtsa.gov/recalls/recallsByVehicle"

def get_vehicle_info(vin: str, year: Optional[str] = None) -> Dict[str, Any]:
    """Decode VIN and return basic vehicle details"""

    if not vin or len(vin) != 17:
        return {"error": "VIN must be 17 characters"}

    try:
        params = {"format": "json"}
        if year:
            params["modelyear"] = year

        res = requests.get(f"{VIN_API}/{vin}", params=params, timeout=10)
        res.raise_for_status()

        data = res.json().get("Results", [{}])[0]

        return {
            "make": data.get("Make"),
            "model": data.get("Model"),
            "year": data.get("ModelYear"),
            "body": data.get("BodyClass"),
            "fuel": data.get("FuelTypePrimary"),
            "manufacturer": data.get("Manufacturer"),
        }

    except Exception as e:
        return {"error": str(e)}
def get_recalls(make: str, model: str, year: str) -> Dict[str, Any]:
    """Fetch recall information for the vehicle"""

    if not all([make, model, year]):
        return {"error": "make, model, year required"}

    try:
        res = requests.get(
            RECALL_API,
            params={"make": make, "model": model, "modelYear": year},
            timeout=10,
        )
        res.raise_for_status()

        recalls = res.json().get("results", [])

        return {
            "recall_count": len(recalls),
            "recalls": [
                {
                    "campaign": r.get("NHTSACampaignNumber"),
                    "summary": r.get("Summary"),
                    "remedy": r.get("Remedy"),
                }
                for r in recalls[:5]
            ],
        }
    except Exception as e:
        return {"error": str(e)}