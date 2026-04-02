from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True, index=True)
    full_name    = Column(String(100))
    email        = Column(String(200), unique=True, index=True, nullable=False)
    password     = Column(String(200), nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow)

    contracts    = relationship("Contract", back_populates="owner")


class Contract(Base):
    __tablename__ = "contracts"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename       = Column(String(300))
    raw_text       = Column(Text)
    fairness_score = Column(Float, nullable=True)
    uploaded_at    = Column(DateTime, default=datetime.utcnow)

    owner          = relationship("User", back_populates="contracts")
    sla            = relationship("ContractSLA", back_populates="contract", uselist=False)
    flags          = relationship("ContractFlag", back_populates="contract")
    messages       = relationship("ChatMessage", back_populates="contract")


class ContractSLA(Base):
    __tablename__ = "contract_sla"

    id                   = Column(Integer, primary_key=True, index=True)
    contract_id          = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    apr                  = Column(Float, nullable=True)
    term_months          = Column(Integer, nullable=True)
    monthly_payment      = Column(Float, nullable=True)
    down_payment         = Column(Float, nullable=True)
    mileage_allowance    = Column(Integer, nullable=True)
    mileage_overage_fee  = Column(Float, nullable=True)
    residual_value       = Column(Float, nullable=True)
    early_termination    = Column(Float, nullable=True)
    buyout_price         = Column(Float, nullable=True)
    warranty_summary     = Column(Text, nullable=True)

    contract             = relationship("Contract", back_populates="sla")


class ContractFlag(Base):
    __tablename__ = "contract_flags"

    id          = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    severity    = Column(String(10))   # "red", "yellow", "green"
    message     = Column(Text)

    contract    = relationship("Contract", back_populates="flags")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id          = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    role        = Column(String(20))   # "user" or "assistant"
    content     = Column(Text)
    created_at  = Column(DateTime, default=datetime.utcnow)

    contract    = relationship("Contract", back_populates="messages")
