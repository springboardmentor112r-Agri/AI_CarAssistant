from typing import List, Optional
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from app.models import RoleEnum

class MessageBase(BaseModel):
    content: str
    role: RoleEnum

class MessageCreate(BaseModel):
    content: str

class MessageResponse(MessageBase):
    id: uuid.UUID
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    created_at: datetime
    messages: List[MessageResponse] = []
    model_config = ConfigDict(from_attributes=True)
