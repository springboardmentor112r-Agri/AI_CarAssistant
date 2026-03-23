from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Document

router = APIRouter()


@router.get("/")
async def compare_contracts(
    doc_id_1: str,
    doc_id_2: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare two contracts side by side.
    Both must belong to current user and be ready.
    Returns structured comparison data.
    """
    results = []
    for doc_id in [doc_id_1, doc_id_2]:
        try:
            uid = UUID(doc_id)
        except ValueError:
            raise HTTPException(400, f"Invalid document ID: {doc_id}")

        result = await db.execute(
            select(Document).where(
                Document.doc_id == uid,
                Document.user_id == current_user.user_id,
            )
        )
        doc = result.scalar_one_or_none()

        if not doc:
            raise HTTPException(404, f"Document {doc_id} not found")
        if doc.processing_status != "ready":
            raise HTTPException(
                400,
                f"Document '{doc.filename}' is not ready for comparison.",
            )
        results.append(doc)

    doc1, doc2 = results

    def extract_fields(doc) -> dict:
        sla = doc.sla_json or {}
        return {
            "doc_id": str(doc.doc_id),
            "filename": doc.filename,
            "fairness_score": doc.contract_fairness_score,
            "red_flags": sla.get("red_flags") or [],
            # Contract info
            "contract_type": sla.get("contract_type"),
            "vin": sla.get("vin"),
            "vehicle_make": sla.get("vehicle_make"),
            "vehicle_model": sla.get("vehicle_model"),
            "vehicle_year": sla.get("vehicle_year"),
            # Terms
            "lease_term": sla.get("lease_term"),
            "loan_term": sla.get("loan_term"),
            "mileage_allowance": sla.get("mileage_allowance"),
            # Financial
            "apr": sla.get("apr"),
            "monthly_payment": sla.get("monthly_payment"),
            "down_payment": sla.get("down_payment"),
            "loan_amount": sla.get("loan_amount"),
            "residual_value": sla.get("residual_value"),
            "acquisition_fee": sla.get("acquisition_fee"),
            "early_termination_fee": sla.get("early_termination_fee"),
            "mileage_overage_charge": sla.get("mileage_overage_charge"),
            "disposition_fee": sla.get("disposition_fee"),
        }

    contract1 = extract_fields(doc1)
    contract2 = extract_fields(doc2)

    def get_winner(field: str, lower_is_better: bool = True) -> str | None:
        v1 = contract1.get(field)
        v2 = contract2.get(field)
        if v1 is None or v2 is None:
            return None
        try:
            n1 = float(
                str(v1).replace("%", "").replace("$", "").replace(",", "").strip()
            )
            n2 = float(
                str(v2).replace("%", "").replace("$", "").replace(",", "").strip()
            )
            if n1 == n2:
                return "tie"
            if lower_is_better:
                return "contract1" if n1 < n2 else "contract2"
            else:
                return "contract1" if n1 > n2 else "contract2"
        except (ValueError, TypeError):
            return None

    winners = {
        "apr": get_winner("apr"),
        "monthly_payment": get_winner("monthly_payment"),
        "down_payment": get_winner("down_payment"),
        "acquisition_fee": get_winner("acquisition_fee"),
        "early_termination_fee": get_winner("early_termination_fee"),
        "mileage_overage_charge": get_winner("mileage_overage_charge"),
        "disposition_fee": get_winner("disposition_fee"),
        "fairness_score": get_winner("fairness_score", lower_is_better=False),
    }

    overall = None
    s1 = contract1.get("fairness_score")
    s2 = contract2.get("fairness_score")
    if s1 is not None and s2 is not None:
        if s1 > s2:
            overall = "contract1"
        elif s2 > s1:
            overall = "contract2"
        else:
            overall = "tie"

    return {
        "contract1": contract1,
        "contract2": contract2,
        "winners": winners,
        "overall_winner": overall,
    }
