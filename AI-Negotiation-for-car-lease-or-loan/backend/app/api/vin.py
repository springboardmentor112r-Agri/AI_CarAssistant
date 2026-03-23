from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Document
from app.services.vin_service import vin_service
from app.services.document_service import get_document

router = APIRouter()

@router.get("/lookup/{vin}")
async def lookup_vin(
    vin: str,
    doc_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Look up VIN details. If doc_id is provided, associate the VIN with the document.
    """
    vin = vin.upper().strip()
    
    if len(vin) < 5 or len(vin) > 20:
        raise HTTPException(status_code=422, detail="Invalid VIN length")
    
    report = await vin_service.get_full_vin_report(
        vin,
        user_id=current_user.user_id,
        doc_id=doc_id
    )
    
    # If doc_id provided and VIN is supported, update document
    if doc_id and report.get("supported"):
        try:
            # Verify document ownership and update
            stmt = (
                update(Document)
                .where(Document.doc_id == doc_id)
                .where(Document.user_id == current_user.user_id)
                .values(vin=vin)
            )
            await db.execute(stmt)
            await db.commit()
        except Exception:
            # Fallback for document service or db issues - we still want to return the report
            pass
            
    return report

@router.get("/from-document/{doc_id}")
async def vin_from_document(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get VIN report based on VIN extracted in a document.
    """
    doc = await get_document(db, doc_id, current_user.user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    vin = doc.sla_json.get("vin") if doc.sla_json else None
    
    if not vin:
        return {
            "supported": False,
            "message": "No VIN found in this contract.",
            "manual_entry_allowed": True,
            "hint": "You can enter the VIN manually using GET /vin/lookup/{vin}"
        }
    
    return await vin_service.get_full_vin_report(
        vin,
        user_id=current_user.user_id,
        doc_id=doc_id
    )
