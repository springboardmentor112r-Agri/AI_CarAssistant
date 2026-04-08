import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, Enum, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base

# Fallback UUID type for SQLite compatibility during local dev
from sqlalchemy.types import TypeDecorator, CHAR
class GUID(TypeDecorator):
    impl = CHAR
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value

class ContractStatus(str, enum.Enum):
    PENDING = "PENDING"
    EXTRACTING = "EXTRACTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class RoleEnum(str, enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"

class User(Base):
    __tablename__ = "users"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contracts = relationship("Contract", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    file_url = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    status = Column(Enum(ContractStatus), default=ContractStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="contracts")
    extracted_sla = relationship("ExtractedSLA", back_populates="contract", uselist=False)
    vehicle = relationship("Vehicle", back_populates="contract", uselist=False)
    conversations = relationship("Conversation", back_populates="contract")

class ExtractedSLA(Base):
    __tablename__ = "extracted_slas"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    contract_id = Column(GUID(), ForeignKey("contracts.id"), unique=True)
    apr = Column(Float, nullable=True)
    lease_term_months = Column(Integer, nullable=True)
    monthly_payment = Column(Float, nullable=True)
    down_payment = Column(Float, nullable=True)
    residual_value = Column(Float, nullable=True)
    mileage_allowance = Column(Integer, nullable=True)
    overage_charge_per_mile = Column(Float, nullable=True)
    early_termination_clause = Column(Text, nullable=True)
    buyout_price = Column(Float, nullable=True)
    fairness_score = Column(Integer, nullable=True)
    red_flags = Column(JSON, nullable=True)
    extracted_at = Column(DateTime, default=datetime.utcnow)

    contract = relationship("Contract", back_populates="extracted_sla")

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    contract_id = Column(GUID(), ForeignKey("contracts.id"))
    vin = Column(String, nullable=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    recalls = Column(JSON, nullable=True)
    fair_price_min = Column(Float, nullable=True)
    fair_price_max = Column(Float, nullable=True)
    fair_price_avg = Column(Float, nullable=True)

    contract = relationship("Contract", back_populates="vehicle")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    contract_id = Column(GUID(), ForeignKey("contracts.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    contract = relationship("Contract", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(GUID(), ForeignKey("conversations.id"))
    role = Column(Enum(RoleEnum), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
