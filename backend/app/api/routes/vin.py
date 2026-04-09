from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Vehicle, VehicleRecall
from app.schemas import VINReportOut, VehicleOut, RecallOut
from app.services.vin_service import decode_vin, get_recalls

router = APIRouter(prefix="/vin", tags=["vin"])


@router.get("/{vin}", response_model=VINReportOut)
async def lookup_vin(
    vin: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vin = vin.strip().upper()
    if len(vin) != 17:
        raise HTTPException(status_code=400, detail="VIN must be exactly 17 characters")

    # Check DB cache first
    existing = db.query(Vehicle).filter(Vehicle.vin == vin).first()
    if existing and existing.recalls:
        return VINReportOut(
            vehicle=VehicleOut.model_validate(existing),
            recalls=[RecallOut.model_validate(r) for r in existing.recalls],
        )

    # Fetch from NHTSA
    vehicle_data = await decode_vin(vin)
    if not vehicle_data:
        raise HTTPException(status_code=404, detail="VIN not found in NHTSA database")

    # Save to DB
    if not existing:
        vehicle = Vehicle(**{k: v for k, v in vehicle_data.items() if k in [
            "vin", "year", "make", "model", "trim", "body_class", "engine", "drivetrain", "fuel_type"
        ]})
        db.add(vehicle)
        db.flush()
    else:
        vehicle = existing

    # Fetch recalls
    recalls_raw = []
    if vehicle_data.get("make") and vehicle_data.get("model") and vehicle_data.get("year"):
        recalls_raw = await get_recalls(vehicle_data["make"], vehicle_data["model"], vehicle_data["year"])

    recall_objs = []
    for r in recalls_raw:
        recall = VehicleRecall(
            vehicle_id=vehicle.id,
            recall_number=r.get("recall_number"),
            issue_date=r.get("issue_date"),
            component=r.get("component"),
            summary=r.get("summary"),
            remedy=r.get("remedy"),
            source=r.get("source", "NHTSA"),
            raw=r.get("raw"),
        )
        db.add(recall)
        recall_objs.append(recall)

    db.commit()
    db.refresh(vehicle)

    return VINReportOut(
        vehicle=VehicleOut.model_validate(vehicle),
        recalls=[RecallOut(
            recall_number=r.recall_number,
            issue_date=r.issue_date,
            component=r.component,
            summary=r.summary,
            remedy=r.remedy,
        ) for r in recall_objs],
    )