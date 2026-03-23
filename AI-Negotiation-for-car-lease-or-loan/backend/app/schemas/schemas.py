from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID
    email: str
    full_name: Optional[str]
    created_at: datetime
    is_active: bool

class SLAJson(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    apr: Optional[str] = None
    lease_term: Optional[str] = None
    monthly_payment: Optional[str] = None
    down_payment: Optional[str] = None
    residual_value: Optional[str] = None
    mileage_allowance: Optional[str] = None
    mileage_overage_charge: Optional[str] = None
    early_termination_fee: Optional[str] = None
    buyout_price: Optional[str] = None
    maintenance_responsibility: Optional[str] = None
    warranty: Optional[str] = None
    late_fee: Optional[str] = None
    gap_coverage: Optional[str] = None
    vin: Optional[str] = None
    red_flags: Optional[List[str]] = []

class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    doc_id: UUID
    user_id: UUID
    filename: str
    sla_json: Optional[dict] = None
    contract_fairness_score: Optional[float] = None
    vin: Optional[str] = None
    upload_timestamp: datetime
    processing_status: str
    sla_retry_count: int = 0
    error_message: Optional[str] = None

class DocumentDetail(DocumentRead):
    model_config = ConfigDict(from_attributes=True)
    raw_extracted_text: Optional[str] = None

class ChatMessageCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    doc_id: UUID
    thread_id: UUID
    message: str

class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message_id: UUID
    thread_id: UUID
    doc_id: UUID
    role: str
    content: str
    timestamp: datetime

class Token(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token: str
    token_type: str
    user: UserRead

class ThreadSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    thread_id: UUID
    first_message_preview: str
    last_updated: datetime

class NewThreadRequest(BaseModel):
    doc_id: UUID
