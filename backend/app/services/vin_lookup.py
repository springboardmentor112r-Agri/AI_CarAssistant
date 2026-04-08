import httpx
from typing import Optional, Dict

async def fetch_vin_details(vin: str) -> Optional[Dict]:
    """
    Fetches vehicle details from the public NHTSA API using a VIN.
    """
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if "Results" in data and len(data["Results"]) > 0:
                    result = data["Results"][0]
                    return {
                        "make": result.get("Make"),
                        "model": result.get("Model"),
                        "year": int(result.get("ModelYear")) if result.get("ModelYear") else None,
                        # Other fields can be extracted here as needed
                    }
    except Exception as e:
        print(f"Error fetching VIN details for {vin}: {e}")
        
    return None
