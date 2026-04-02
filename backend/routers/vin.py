from fastapi import APIRouter, HTTPException
from services.vin_service import lookup_vin

router = APIRouter()


@router.get("/{vin}")
async def get_vin_info(vin: str):
    vin = vin.strip().upper()
    if len(vin) != 17:
        raise HTTPException(status_code=400, detail="VIN must be exactly 17 characters")

    data = await lookup_vin(vin)
    if not data:
        raise HTTPException(status_code=404, detail="VIN not found or invalid")
    return data
