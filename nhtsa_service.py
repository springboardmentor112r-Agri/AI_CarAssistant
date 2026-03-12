import requests
from typing import Dict, Any

VIN_API = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues"
RECALL_API = "https://api.nhtsa.gov/recalls/recallsByVehicle"


def get_vehicle_info(vin: str) -> Dict[str, Any]:
    """Decode VIN to vehicle information"""
    try:
        response = requests.get(
            f"{VIN_API}/{vin}",
            params={"format": "json"},
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("Results", [])

        if not results:
            return {"error": "VIN decode failed"}

        v = results[0]

        return {
            "make": v.get("Make"),
            "model": v.get("Model"),
            "year": v.get("ModelYear"),
            "series": v.get("Series"),
            "trim": v.get("Trim"),
            "vehicle_type": v.get("VehicleType"),
            "body_class": v.get("BodyClass"),
            "doors": v.get("Doors"),
            "drive_type": v.get("DriveType"),
            "engine_cylinders": v.get("EngineCylinders"),
            "fuel_type": v.get("FuelTypePrimary"),
            "manufacturer": v.get("Manufacturer"),
        }

    except Exception as e:
        return {"error": f"VIN API failed: {e}"}


def get_recalls(make: str, model: str, year: str) -> Dict[str, Any]:
    """Fetch vehicle recall data"""

    if not (make and model and year):
        return {"error": "Missing vehicle information"}

    try:
        response = requests.get(
            RECALL_API,
            params={"make": make, "model": model, "modelYear": year},
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        recalls = data.get("results", [])

        return {
            "recall_count": len(recalls),
            "recalls": [
                {
                    "campaign": r.get("NHTSACampaignID"),
                    "component": r.get("Component"),
                    "summary": r.get("Summary"),
                    "consequence": r.get("Consequence"),
                    "remedy": r.get("Remedy"),
                    "date": r.get("ReportReceivedDate"),
                }
                for r in recalls[:5]
            ]
        }

    except Exception as e:
        return {"error": f"Recall API failed: {e}"}