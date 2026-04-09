from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Contract, PriceRecommendation, OfferComparison, Vehicle
from app.schemas import PriceRecOut, CompareRequest, CompareOut, SLAOut
from app.services.price_service import estimate_price
from app.services.llm_service import compare_deals
import json

router = APIRouter(prefix="/price", tags=["price"])


@router.get("/estimate/{vehicle_id}", response_model=PriceRecOut)
async def price_estimate(
    vehicle_id: int,
    postal_code: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    data = await estimate_price(
        make=vehicle.make or "",
        model=vehicle.model or "",
        year=vehicle.year or 2024,
        postal_code=postal_code,
    )

    rec = PriceRecommendation(
        vehicle_id=vehicle_id,
        geo_postal=postal_code,
        **{k: v for k, v in data.items() if k in ["msrp", "fair_price_low", "fair_price_high", "basis", "methodology"]},
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return PriceRecOut.model_validate(rec)


@router.post("/compare", response_model=CompareOut)
def compare_contracts(
    payload: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    def get_sla_dict(contract_id: int):
        c = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == current_user.id).first()
        if not c:
            raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
        if not c.sla:
            raise HTTPException(status_code=400, detail=f"Contract {contract_id} has no extracted SLA yet")
        return SLAOut.model_validate(c.sla).model_dump()

    deal1 = get_sla_dict(payload.primary_contract_id)
    deal2 = get_sla_dict(payload.compared_contract_id)

    analysis = compare_deals(deal1, deal2)

    comparison = OfferComparison(
        user_id=current_user.id,
        primary_contract_id=payload.primary_contract_id,
        compared_contract_id=payload.compared_contract_id,
        comparison_json=analysis,
    )
    db.add(comparison)
    db.commit()

    primary_sla = db.query(Contract).filter(Contract.id == payload.primary_contract_id).first().sla
    compared_sla = db.query(Contract).filter(Contract.id == payload.compared_contract_id).first().sla

    return CompareOut(
        primary=SLAOut.model_validate(primary_sla),
        compared=SLAOut.model_validate(compared_sla),
        analysis=analysis.get("analysis", ""),
        winner=analysis.get("winner", "unknown"),
    )