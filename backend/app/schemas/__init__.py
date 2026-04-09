from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Contract ──────────────────────────────────────────────────────────────────
class ContractOut(BaseModel):
    id: int
    contract_type: Optional[str]
    doc_status: str
    dealer_offer_name: Optional[str]
    contract_date: Optional[str]
    fairness_score: Optional[float]
    red_flag_level: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ContractListOut(BaseModel):
    contracts: List[ContractOut]
    total: int


# ── SLA ───────────────────────────────────────────────────────────────────────
class SLAOut(BaseModel):
    id: int
    contract_id: int
    apr_percent: Optional[float]
    money_factor: Optional[float]
    term_months: Optional[int]
    monthly_payment: Optional[float]
    down_payment: Optional[float]
    fees_total: Optional[float]
    residual_value: Optional[float]
    residual_percent_msrp: Optional[float]
    msrp: Optional[float]
    cap_cost: Optional[float]
    cap_cost_reduction: Optional[float]
    mileage_allowance_yr: Optional[int]
    mileage_overage_fee: Optional[float]
    early_termination_fee: Optional[float]
    disposition_fee: Optional[float]
    purchase_option_price: Optional[float]
    insurance_requirements: Optional[str]
    maintenance_resp: Optional[str]
    warranty_summary: Optional[str]
    late_fee_policy: Optional[str]
    other_terms: Optional[Any]

    class Config:
        from_attributes = True


# ── Vehicle / VIN ─────────────────────────────────────────────────────────────
class VehicleOut(BaseModel):
    id: int
    vin: Optional[str]
    year: Optional[int]
    make: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    body_class: Optional[str]
    fuel_type: Optional[str]

    class Config:
        from_attributes = True


class RecallOut(BaseModel):
    recall_number: Optional[str]
    issue_date: Optional[str]
    component: Optional[str]
    summary: Optional[str]
    remedy: Optional[str]

    class Config:
        from_attributes = True


class VINReportOut(BaseModel):
    vehicle: VehicleOut
    recalls: List[RecallOut]


# ── Extracted Clauses ─────────────────────────────────────────────────────────
class ClauseOut(BaseModel):
    id: int
    clause_type: Optional[str]
    page_number: Optional[int]
    text_snippet: Optional[str]
    normalized_value: Optional[Any]
    red_flag_level: Optional[str]
    comment: Optional[str]

    class Config:
        from_attributes = True


# ── Negotiation ───────────────────────────────────────────────────────────────
class ChatMessageIn(BaseModel):
    contract_id: Optional[int] = None
    thread_id: Optional[int] = None
    message: str


class ChatMessageOut(BaseModel):
    thread_id: int
    response: str
    suggested_message: Optional[str] = None


class NegotiationMessageOut(BaseModel):
    id: int
    sender_role: str
    body: str
    suggested_text: Optional[str]
    sent_at: datetime

    class Config:
        from_attributes = True


class ThreadOut(BaseModel):
    id: int
    subject: Optional[str]
    created_at: datetime
    messages: List[NegotiationMessageOut] = []

    class Config:
        from_attributes = True


# ── Price ─────────────────────────────────────────────────────────────────────
class PriceRecOut(BaseModel):
    vehicle_id: int
    geo_postal: Optional[str]
    msrp: Optional[float]
    fair_price_low: Optional[float]
    fair_price_high: Optional[float]
    basis: Optional[str]
    methodology: Optional[str]

    class Config:
        from_attributes = True


# ── Offer Comparison ──────────────────────────────────────────────────────────
class CompareRequest(BaseModel):
    primary_contract_id: int
    compared_contract_id: int


class CompareOut(BaseModel):
    primary: SLAOut
    compared: SLAOut
    analysis: str
    winner: str