from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, Contract, ContractSLA, ContractFlag
from utils.auth_utils import get_current_user
from services.llm_service import extract_sla_with_llm, compute_fairness_score, generate_flags

router = APIRouter()


@router.post("/{contract_id}/analyze")
def analyze_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(
        Contract.id == contract_id, Contract.user_id == current_user.id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if not contract.raw_text:
        raise HTTPException(status_code=400, detail="Contract has no extracted text")

    # LLM extraction
    sla_data = extract_sla_with_llm(contract.raw_text)

    # Upsert SLA
    existing_sla = db.query(ContractSLA).filter(ContractSLA.contract_id == contract_id).first()
    if existing_sla:
        for k, v in sla_data.items():
            setattr(existing_sla, k, v)
    else:
        sla_obj = ContractSLA(contract_id=contract_id, **sla_data)
        db.add(sla_obj)

    # Fairness score + flags
    score = compute_fairness_score(sla_data)
    flags = generate_flags(sla_data)

    contract.fairness_score = score

    # Replace old flags
    db.query(ContractFlag).filter(ContractFlag.contract_id == contract_id).delete()
    for flag in flags:
        db.add(ContractFlag(contract_id=contract_id, severity=flag["severity"], message=flag["message"]))

    db.commit()

    return {
        "contract_id": contract_id,
        "fairness_score": score,
        "sla": sla_data,
        "flags": flags,
    }


@router.get("/{contract_id}/results")
def get_results(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(
        Contract.id == contract_id, Contract.user_id == current_user.id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return {
        "fairness_score": contract.fairness_score,
        "sla": contract.sla,
        "flags": [{"severity": f.severity, "message": f.message} for f in contract.flags],
    }
