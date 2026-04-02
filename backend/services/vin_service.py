import httpx

NHTSA_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{}?format=json"
RECALL_URL = "https://api.nhtsa.gov/recalls/recallsByVehicle?make={}&model={}&modelYear={}"


async def lookup_vin(vin: str) -> dict | None:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(NHTSA_URL.format(vin))
        if resp.status_code != 200:
            return None

        data = resp.json().get("Results", [])
        parsed = {item["Variable"]: item["Value"] for item in data if item["Value"] not in (None, "", "Not Applicable")}

        make  = parsed.get("Make", "Unknown")
        model = parsed.get("Model", "Unknown")
        year  = parsed.get("Model Year", "Unknown")

        # Fetch recalls
        recalls = await _get_recalls(client, make, model, year)

        return {
            "vin": vin,
            "make": make,
            "model": model,
            "year": year,
            "trim": parsed.get("Trim", ""),
            "engine": parsed.get("Displacement (L)", "") + "L " + parsed.get("Engine Configuration", ""),
            "body_class": parsed.get("Body Class", ""),
            "drive_type": parsed.get("Drive Type", ""),
            "fuel_type": parsed.get("Fuel Type - Primary", ""),
            "country": parsed.get("Plant Country", ""),
            "recall_count": len(recalls),
            "recalls": recalls[:3],   # Return top 3 recalls
        }


async def _get_recalls(client: httpx.AsyncClient, make: str, model: str, year: str) -> list:
    try:
        url = RECALL_URL.format(make, model, year)
        resp = await client.get(url)
        if resp.status_code != 200:
            return []
        results = resp.json().get("results", [])
        return [
            {
                "component": r.get("Component", ""),
                "summary": r.get("Summary", "")[:200],
                "remedy": r.get("Remedy", ""),
            }
            for r in results
        ]
    except Exception:
        return []
