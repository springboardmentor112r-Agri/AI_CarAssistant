from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Contract, NegotiationThread, NegotiationMessage
from app.schemas import ChatMessageIn, ChatMessageOut, ThreadOut, NegotiationMessageOut
from app.services.llm_service import get_negotiation_response
import json

router = APIRouter(prefix="/negotiation", tags=["negotiation"])


def _build_contract_context(contract: Contract) -> str:
    if not contract or not contract.sla:
        return "No contract data available."
    sla = contract.sla
    return (
        f"Contract Type: {contract.contract_type}\n"
        f"Monthly Payment: ${sla.monthly_payment}\n"
        f"APR: {sla.apr_percent}%\n"
        f"Term: {sla.term_months} months\n"
        f"Down Payment: ${sla.down_payment}\n"
        f"MSRP: ${sla.msrp}\n"
        f"Residual Value: ${sla.residual_value}\n"
        f"Mileage Allowance: {sla.mileage_allowance_yr} miles/year\n"
        f"Early Termination Fee: ${sla.early_termination_fee}\n"
        f"Fairness Score: {contract.fairness_score}/100\n"
        f"Red Flag Level: {contract.red_flag_level}"
    )


@router.post("/chat", response_model=ChatMessageOut)
async def chat(
    payload: ChatMessageIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get or create thread
    thread = None
    if payload.thread_id:
        thread = db.query(NegotiationThread).filter(
            NegotiationThread.id == payload.thread_id,
            NegotiationThread.user_id == current_user.id
        ).first()

    if not thread:
        contract_id = payload.contract_id
        thread = NegotiationThread(
            user_id=current_user.id,
            contract_id=contract_id,
            subject=payload.message[:60],
        )
        db.add(thread)
        db.flush()

    # Build contract context
    contract_context = ""
    if thread.contract_id:
        contract = db.query(Contract).filter(Contract.id == thread.contract_id).first()
        contract_context = _build_contract_context(contract)

    # Call LLM
    ai_result = get_negotiation_response(contract_context, payload.message)

    # Save user message
    user_msg = NegotiationMessage(
        thread_id=thread.id,
        sender_role="user",
        body=payload.message,
    )
    db.add(user_msg)

    # Save AI response
    ai_msg = NegotiationMessage(
        thread_id=thread.id,
        sender_role="assistant",
        body=ai_result.get("response", ""),
        suggested_text=ai_result.get("suggested_dealer_message", ""),
    )
    db.add(ai_msg)
    db.commit()

    return ChatMessageOut(
        thread_id=thread.id,
        response=ai_result.get("response", ""),
        suggested_message=ai_result.get("suggested_dealer_message"),
    )


@router.get("/threads", response_model=List[ThreadOut])
def list_threads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    threads = db.query(NegotiationThread).filter(NegotiationThread.user_id == current_user.id).all()
    result = []
    for t in threads:
        msgs = [NegotiationMessageOut.model_validate(m) for m in t.messages]
        result.append(ThreadOut(id=t.id, subject=t.subject, created_at=t.created_at, messages=msgs))
    return result


@router.get("/threads/{thread_id}", response_model=ThreadOut)
def get_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    thread = db.query(NegotiationThread).filter(
        NegotiationThread.id == thread_id,
        NegotiationThread.user_id == current_user.id
    ).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    msgs = [NegotiationMessageOut.model_validate(m) for m in thread.messages]
    return ThreadOut(id=thread.id, subject=thread.subject, created_at=thread.created_at, messages=msgs)