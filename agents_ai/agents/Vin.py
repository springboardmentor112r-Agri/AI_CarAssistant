import re
import requests

# --------------------------
# VIN Extraction
# --------------------------
import re

def extract_vin(contract_text: str):
    """
    Extracts a VIN from the text.
    Returns the first 17-character VIN if available.
    Otherwise, returns the first shorter VIN-like code (6-16 chars) containing at least one digit.
    Returns None if no VIN-like value is found.
    """
    # Try full VIN first (17 characters)
    full_vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
    full_matches = re.findall(full_vin_pattern, contract_text)
    if full_matches:
        return full_matches[0]

    # Fallback: shorter VIN-like codes (6-16 chars, must contain a digit)
    short_vin_pattern = r'\b[A-HJ-NPR-Z0-9]{6,16}\b'
    short_matches = re.findall(short_vin_pattern, contract_text)
    for vin in short_matches:
        if any(c.isdigit() for c in vin):
            return vin

    # Nothing found
    return None
# --------------------------
# Vehicle Data Lookup
# --------------------------
def fetch_vehicle_data(vin: str):
    """
    Fetch vehicle information from the NHTSA API for a given VIN.
    Returns a dictionary with keys: 'Make', 'Model', 'Model Year', or 'error'.
    """
    api_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        results = response.json().get("Results", [])
        vehicle_data = {item["Variable"]: item["Value"] 
                        for item in results 
                        if item["Variable"] in ["Make", "Model", "Model Year"]}

        return vehicle_data

    except Exception as e:
        return {"error": f"VIN lookup failed: {str(e)}"}

















# import re
# import requests

# def extract_vin(contract_text: str):
#     vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
#     matches = re.findall(vin_pattern, contract_text)
#     return matches[0] if matches else None


# def fetch_vehicle_data(vin: str):
#     api_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"

#     try:
#         response = requests.get(api_url, timeout=10)
#         response.raise_for_status()

#         results = response.json().get("Results", [])

#         vehicle_data = {}

#         for item in results:
#             if item["Variable"] in ["Make", "Model", "Model Year"]:
#                 vehicle_data[item["Variable"]] = item["Value"]

#         return vehicle_data

#     except Exception as e:
#         return {"error": f"VIN lookup failed: {str(e)}"}