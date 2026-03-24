import requests
from typing import Dict, Any
from datetime import datetime

# NHTSA APIs
VIN_API = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues"
RECALL_API = "https://api.nhtsa.gov/recalls/recallsByVehicle"


def estimate_price(year: str) -> str:
    """
    Simple depreciation-based price estimation.
    """
    try:
        current_year = datetime.now().year
        age = current_year - int(year)

        base_price = 35000
        depreciation = 0.15

        price = base_price * ((1 - depreciation) ** age)

        return f"${round(price,2)}"

    except:
        return "Unknown"


def get_vehicle_info(vin: str) -> Dict[str, Any]:
    """
    Decode VIN to detailed vehicle information.
    """
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

        vehicle_details = {
            "vin": vin,
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

        return vehicle_details

    except Exception as e:
        return {"error": f"VIN API failed: {e}"}


def get_recalls(make: str, model: str, year: str) -> Dict[str, Any]:
    """
    Fetch vehicle recall data using make, model, and year.
    """
    if not (make and model and year):
        return {"error": "Missing vehicle information for recalls"}

    try:
        response = requests.get(
            RECALL_API,
            params={"make": make, "model": model, "modelYear": year},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        recalls = data.get("results", [])

        recalls_list = [
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

        return {
            "recall_count": len(recalls),
            "recalls": recalls_list
        }

    except Exception as e:
        return {"error": f"Recall API failed: {e}"}


def generate_vin_report(vin: str) -> Dict[str, Any]:
    """
    Generate VIN report with VIN first and then vehicle details.
    """

    vehicle_info = get_vehicle_info(vin)

    if "error" in vehicle_info:
        return vehicle_info

    # ADD PRICE HERE
    estimated_price = estimate_price(vehicle_info.get("year"))

    return {
        "vin": vin,
        "vehicle_details": vehicle_info,
        "estimated_price": estimated_price
    }


# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":
    test_vin = "1HGCM82633A004352"
    report = generate_vin_report(test_vin)

    from pprint import pprint
    pprint(report)