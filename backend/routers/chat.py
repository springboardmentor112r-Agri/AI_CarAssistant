from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import User, Contract, ChatMessage
from utils.auth_utils import get_current_user
from services.llm_service import get_negotiation_response

router = APIRouter()


class ChatRequest(BaseModel):
    contract_id: int
    message: str


@router.post("/")
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(
        Contract.id == body.contract_id,
        Contract.user_id == current_user.id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get chat history for context
    history = db.query(ChatMessage).filter(
        ChatMessage.contract_id == body.contract_id
    ).order_by(ChatMessage.created_at).all()

    messages_ctx = [{"role": m.role, "content": m.content} for m in history[-10:]]

    # Build SLA context string
    sla_context = ""
    if contract.sla:
        s = contract.sla
        sla_context = (
            f"Contract SLA: APR={s.apr}%, Monthly=${s.monthly_payment}, "
            f"Term={s.term_months}mo, Down=${s.down_payment}, "
            f"Mileage={s.mileage_allowance}/yr at ${s.mileage_overage_fee}/mi overage, "
            f"Early exit fee=${s.early_termination}, Residual={s.residual_value}%, "
            f"Fairness Score={contract.fairness_score}/100"
        )

    # Get AI response
    ai_reply = get_negotiation_response(body.message, messages_ctx, sla_context)

    # Save both messages
    db.add(ChatMessage(contract_id=body.contract_id, role="user", content=body.message))
    db.add(ChatMessage(contract_id=body.contract_id, role="assistant", content=ai_reply))
    db.commit()

    return {"reply": ai_reply}


@router.get("/{contract_id}/history")
def get_history(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = db.query(Contract).filter(
        Contract.id == contract_id, Contract.user_id == current_user.id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    messages = db.query(ChatMessage).filter(
        ChatMessage.contract_id == contract_id
    ).order_by(ChatMessage.created_at).all()

    return [{"role": m.role, "content": m.content, "time": m.created_at} for m in messages]
