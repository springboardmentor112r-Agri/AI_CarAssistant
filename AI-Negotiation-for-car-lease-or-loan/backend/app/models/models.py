from app.core.database import Base
from sqlalchemy import Column, String, Boolean, Text, Float, DateTime, ForeignKey, func, Integer, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    filename = Column(String(500), nullable=False)
    raw_extracted_text = Column(Text, nullable=True)
    # Stores extracted text from ANY uploaded file format.
    # PDF native    -> pdfplumber text layer
    # PDF scanned   -> Google Vision OCR (pytesseract fallback)
    # Images        -> Google Vision OCR (pytesseract fallback)
    # Word/Excel    -> direct text extraction
    # CSV/TXT/HTML  -> direct text extraction
    # Email         -> body text extraction
    # This is injected directly into LLM context on every chat message.
    sla_json = Column(JSONB, nullable=True)
    contract_fairness_score = Column(Float, nullable=True)
    vin = Column(String(17), nullable=True)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String(50), default="pending")
    # pending
    # processing
    # extraction_complete  (text extracted, waiting for SLA)
    # sla_failed           (LLM failed, user can retry)
    # ready                (SLA extracted, at least 1 core field present)
    # error                (total failure, document deleted)
    error_message = Column(Text, nullable=True)
    sla_retry_count = Column(Integer, default=0, nullable=False, server_default="0")

    user = relationship("User", back_populates="documents")
    chat_history = relationship("ChatHistory", back_populates="document", cascade="all, delete-orphan")

class ChatHistory(Base):
    __tablename__ = "chat_history"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.doc_id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="chat_history")
    user = relationship("User", back_populates="chat_history")

class LLMLog(Base):
  __tablename__ = "llm_logs"

  log_id = Column(
    UUID(as_uuid=True),
    primary_key=True,
    server_default=text("gen_random_uuid()")
  )
  timestamp = Column(
    DateTime(timezone=True),
    server_default=text("now()"),
    nullable=False
  )
  user_id = Column(UUID(as_uuid=True), nullable=True)
  doc_id = Column(UUID(as_uuid=True), nullable=True)
  thread_id = Column(UUID(as_uuid=True), nullable=True)
  module = Column(String(50), nullable=False)
  model = Column(String(100), nullable=True)
  prompt_tokens = Column(Integer, nullable=True)
  completion_tokens = Column(Integer, nullable=True)
  total_tokens = Column(Integer, nullable=True)
  response_time_ms = Column(Integer, nullable=True)
  success = Column(Boolean, nullable=False, default=True)
  error_message = Column(Text, nullable=True)
  cost_estimate_usd = Column(Float, nullable=True)
class RefreshToken(Base):
  __tablename__ = "refresh_tokens"

  id = Column(
    UUID(as_uuid=True),
    primary_key=True,
    server_default=text("gen_random_uuid()")
  )
  user_id = Column(
    UUID(as_uuid=True),
    ForeignKey("users.user_id", ondelete="CASCADE"),
    nullable=False,
    index=True,
  )
  # SHA-256 hash of the JWT string — never store the plain token
  token_hash = Column(String(64), nullable=False, unique=True, index=True)
  expires_at = Column(DateTime(timezone=True), nullable=False)
  revoked = Column(Boolean, nullable=False, default=False)
  created_at = Column(
    DateTime(timezone=True),
    server_default=text("now()"),
    nullable=False,
  )

  user = relationship("User", back_populates="refresh_tokens")


class PasswordResetToken(Base):
  __tablename__ = "password_reset_tokens"

  id = Column(
    UUID(as_uuid=True),
    primary_key=True,
    server_default=text("gen_random_uuid()")
  )
  user_id = Column(
    UUID(as_uuid=True),
    ForeignKey("users.user_id", ondelete="CASCADE"),
    nullable=False,
  )
  # SHA-256 hash of the actual token
  # Never store plain token in DB
  token_hash = Column(String(64), nullable=False, unique=True)
  expires_at = Column(DateTime(timezone=True), nullable=False)
  used = Column(Boolean, nullable=False, default=False)
  created_at = Column(
    DateTime(timezone=True),
    server_default=text("now()"),
    nullable=False,
  )
