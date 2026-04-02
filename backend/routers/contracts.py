from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os, aiofiles, uuid

from database import get_db
from models import User, Contract
from utils.auth_utils import get_current_user
from services.ocr_service import extract_text_from_file

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed = {".pdf", ".png", ".jpg", ".jpeg"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Only PDF or image files allowed")

    # Save file
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # OCR extract
    raw_text = extract_text_from_file(file_path, ext)

    contract = Contract(
        user_id=current_user.id,
        filename=file.filename,
        raw_text=raw_text,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    return {"contract_id": contract.id, "filename": contract.filename, "text_length": len(raw_text)}


@router.get("/")
def list_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contracts = db.query(Contract).filter(Contract.user_id == current_user.id).all()
    return [
        {
            "id": c.id,
            "filename": c.filename,
            "fairness_score": c.fairness_score,
            "uploaded_at": c.uploaded_at,
        }
        for c in contracts
    ]


@router.get("/{contract_id}")
def get_contract(
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
        "id": contract.id,
        "filename": contract.filename,
        "raw_text": contract.raw_text,
        "fairness_score": contract.fairness_score,
        "uploaded_at": contract.uploaded_at,
        "sla": contract.sla,
        "flags": contract.flags,
    }


@router.delete("/{contract_id}")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(
        Contract.id == contract_id, Contract.user_id == current_user.id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    db.delete(contract)
    db.commit()
    return {"message": "Contract deleted"}
