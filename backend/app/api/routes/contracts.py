import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models import User, Contract, ContractFile, ContractSLA, Extraction, ExtractedClause, Vehicle, VehicleRecall
from app.schemas import ContractOut, ContractListOut, SLAOut, ClauseOut
from app.services.ocr_service import extract_text_from_pdf, extract_text_from_image
from app.services.llm_service import extract_sla_from_text
from app.services.vin_service import decode_vin, get_recalls
from app.services.price_service import estimate_price
import asyncio

router = APIRouter(prefix="/contracts", tags=["contracts"])

ALLOWED_MIME = {"application/pdf", "image/jpeg", "image/png", "image/webp", "text/plain"}


def _run_extraction(contract_id: int, file_path: str, mime_type: str):
    """Background task: OCR → LLM extraction → save to DB."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return

        contract.doc_status = "processing"
        db.commit()

        # OCR
        if mime_type == "application/pdf":
            pages = extract_text_from_pdf(file_path)
        elif mime_type == "text/plain":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            pages = [{"page_number": 1, "text": text, "confidence": 1.0}]
        else:
            pages = extract_text_from_image(file_path)

        full_text = "\n".join(p["text"] for p in pages)

        # LLM extraction
        extraction = Extraction(contract_id=contract_id, model_name="gemini-1.5-flash", prompt_version="v1", status="running")
        db.add(extraction)
        db.commit()

        result = extract_sla_from_text(full_text)

        # Save SLA
        sla = ContractSLA(
            contract_id=contract_id,
            apr_percent=result.get("apr_percent"),
            money_factor=result.get("money_factor"),
            term_months=result.get("term_months"),
            monthly_payment=result.get("monthly_payment"),
            down_payment=result.get("down_payment"),
            fees_total=result.get("fees_total"),
            residual_value=result.get("residual_value"),
            residual_percent_msrp=result.get("residual_percent_msrp"),
            msrp=result.get("msrp"),
            cap_cost=result.get("cap_cost"),
            cap_cost_reduction=result.get("cap_cost_reduction"),
            mileage_allowance_yr=result.get("mileage_allowance_yr"),
            mileage_overage_fee=result.get("mileage_overage_fee"),
            early_termination_fee=result.get("early_termination_fee"),
            disposition_fee=result.get("disposition_fee"),
            purchase_option_price=result.get("purchase_option_price"),
            insurance_requirements=result.get("insurance_requirements"),
            maintenance_resp=result.get("maintenance_resp"),
            warranty_summary=result.get("warranty_summary"),
            late_fee_policy=result.get("late_fee_policy"),
        )
        db.add(sla)

        # Save red flags as clauses
        for flag in result.get("red_flags", []):
            clause = ExtractedClause(
                contract_id=contract_id,
                clause_type="red_flag",
                text_snippet=flag,
                red_flag_level="high",
                comment="Identified by AI analysis",
            )
            db.add(clause)

        # Save vehicle if VIN present
        vin = result.get("vehicle_vin")
        if vin:
            existing_vehicle = db.query(Vehicle).filter(Vehicle.vin == vin.upper()).first()
            if not existing_vehicle:
                vehicle = Vehicle(
                    vin=vin.upper(),
                    year=result.get("vehicle_year"),
                    make=result.get("vehicle_make"),
                    model=result.get("vehicle_model"),
                    trim=result.get("vehicle_trim"),
                )
                db.add(vehicle)
                db.flush()
                contract.vehicle_id = vehicle.id
            else:
                contract.vehicle_id = existing_vehicle.id

        contract.fairness_score = result.get("fairness_score")
        contract.red_flag_level = "high" if len(result.get("red_flags", [])) > 2 else "low"
        contract.contract_type = result.get("contract_type", "lease")
        contract.doc_status = "extracted"
        contract.notes = result.get("fairness_explanation", "")

        extraction.status = "completed"
        extraction.raw_output = result
        db.commit()

    except Exception as e:
        db.query(Contract).filter(Contract.id == contract_id).update({"doc_status": "failed"})
        db.commit()
        raise
    finally:
        db.close()


@router.post("/upload", response_model=ContractOut, status_code=201)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dealer_offer_name: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="Only PDF, image, or text files allowed")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    contract = Contract(
        user_id=current_user.id,
        doc_status="uploaded",
        dealer_offer_name=dealer_offer_name or file.filename,
    )
    db.add(contract)
    db.flush()

    cf = ContractFile(
        contract_id=contract.id,
        storage_url=file_path,
        file_name=file.filename,
        mime_type=file.content_type,
    )
    db.add(cf)
    db.commit()
    db.refresh(contract)

    background_tasks.add_task(_run_extraction, contract.id, file_path, file.content_type)
    return ContractOut.model_validate(contract)


@router.get("", response_model=ContractListOut)
def list_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contracts = db.query(Contract).filter(Contract.user_id == current_user.id).all()
    return ContractListOut(contracts=[ContractOut.model_validate(c) for c in contracts], total=len(contracts))


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == current_user.id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractOut.model_validate(contract)


@router.get("/{contract_id}/sla", response_model=SLAOut)
def get_sla(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == current_user.id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if not contract.sla:
        raise HTTPException(status_code=404, detail="SLA not yet extracted")
    return SLAOut.model_validate(contract.sla)


@router.get("/{contract_id}/clauses", response_model=List[ClauseOut])
def get_clauses(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == current_user.id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return [ClauseOut.model_validate(c) for c in contract.extracted_clauses]


@router.delete("/{contract_id}", status_code=204)
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id, Contract.user_id == current_user.id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Delete related records manually first
    from sqlalchemy import text
    db.execute(text(f"DELETE FROM negotiation_messages WHERE thread_id IN (SELECT id FROM negotiation_threads WHERE contract_id = {contract_id})"))
    db.execute(text(f"DELETE FROM negotiation_threads WHERE contract_id = {contract_id}"))
    db.execute(text(f"DELETE FROM extracted_clauses WHERE contract_id = {contract_id}"))
    db.execute(text(f"DELETE FROM extractions WHERE contract_id = {contract_id}"))
    db.execute(text(f"DELETE FROM contract_sla WHERE contract_id = {contract_id}"))
    db.execute(text(f"DELETE FROM contract_files WHERE contract_id = {contract_id}"))
    db.execute(text(f"DELETE FROM contracts WHERE id = {contract_id}"))
    db.commit()