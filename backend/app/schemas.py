from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from app.models import ContractStatus, RoleEnum

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ContractBase(BaseModel):
    status: ContractStatus

class ContractResponse(ContractBase):
    id: uuid.UUID
    user_id: uuid.UUID
    file_url: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ExtractedSLAResponse(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    apr: Optional[float] = None
    lease_term_months: Optional[int] = None
    monthly_payment: Optional[float] = None
    down_payment: Optional[float] = None
    residual_value: Optional[float] = None
    mileage_allowance: Optional[int] = None
    overage_charge_per_mile: Optional[float] = None
    early_termination_clause: Optional[str] = None
    buyout_price: Optional[float] = None
    fairness_score: Optional[int] = None
    red_flags: Optional[Any] = None
    extracted_at: datetime
    model_config = ConfigDict(from_attributes=True)
