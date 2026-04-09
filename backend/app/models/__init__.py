from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(30))
    full_name = Column(String(200))
    hashed_password = Column(String(255), nullable=False)
    auth_provider = Column(String(50), default="local")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contracts = relationship("Contract", back_populates="user")
    negotiation_threads = relationship("NegotiationThread", back_populates="user")


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    vin = Column(String(17), unique=True, index=True)
    year = Column(Integer)
    make = Column(String(100))
    model = Column(String(100))
    trim = Column(String(100))
    body_class = Column(String(100))
    engine = Column(String(100))
    drivetrain = Column(String(100))
    fuel_type = Column(String(60))
    odometer_miles = Column(Float)
    color_ext = Column(String(60))
    color_int = Column(String(60))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    recalls = relationship("VehicleRecall", back_populates="vehicle")
    reports = relationship("VehicleReport", back_populates="vehicle")
    contracts = relationship("Contract", back_populates="vehicle")
    price_recommendations = relationship("PriceRecommendation", back_populates="vehicle")


class VehicleRecall(Base):
    __tablename__ = "vehicle_recalls"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    recall_number = Column(String(50))
    issue_date = Column(String(30))
    component = Column(String(255))
    summary = Column(Text)
    remedy = Column(Text)
    source = Column(String(100))
    raw = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vehicle = relationship("Vehicle", back_populates="recalls")


class VehicleReport(Base):
    __tablename__ = "vehicle_reports"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    title = Column(String(200))
    report_type = Column(String(100))
    availability = Column(String(100))
    url = Column(String(512))
    raw = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vehicle = relationship("Vehicle", back_populates="reports")
    provider = relationship("Provider")


class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    nmls_id = Column(String(50), nullable=True)
    website = Column(String(255))
    send = Column(String(200))
    is_free = Column(Boolean, default=True)
    base_url = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    credentials = relationship("ProviderCredential", back_populates="provider")


class ProviderCredential(Base):
    __tablename__ = "provider_credentials"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    label = Column(String(100))
    config = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    provider = relationship("Provider", back_populates="credentials")


class Dealer(Base):
    __tablename__ = "dealers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(60))
    phone = Column(String(40))
    website = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contracts = relationship("Contract", back_populates="dealer")


class Lender(Base):
    __tablename__ = "lenders"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    nmls_id = Column(String(50))
    website = Column(String(255))
    phone = Column(String(40))
    address = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contracts = relationship("Contract", back_populates="lender")


class ContractTypeEnum(str, enum.Enum):
    lease = "lease"
    loan = "loan"


class DocStatusEnum(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    extracted = "extracted"
    failed = "failed"


class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=True)
    contract_type = Column(Enum(ContractTypeEnum), nullable=True)
    doc_status = Column(Enum(DocStatusEnum), default=DocStatusEnum.uploaded)
    dealer_offer_name = Column(String(200))
    contract_date = Column(String(30))
    locale = Column(String(50), default="en-US")
    currency = Column(String(10), default="USD")
    fairness_score = Column(Float)
    red_flag_level = Column(String(20))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="contracts")
    vehicle = relationship("Vehicle", back_populates="contracts")
    dealer = relationship("Dealer", back_populates="contracts")
    lender = relationship("Lender", back_populates="contracts")
    files = relationship("ContractFile", back_populates="contract")
    sla = relationship("ContractSLA", back_populates="contract", uselist=False)
    extractions = relationship("Extraction", back_populates="contract")
    extracted_clauses = relationship("ExtractedClause", back_populates="contract")
    negotiation_threads = relationship("NegotiationThread", back_populates="contract")


class ContractFile(Base):
    __tablename__ = "contract_files"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    storage_url = Column(String(512))
    file_name = Column(String(255))
    mime_type = Column(String(100))
    page_count = Column(Integer)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="files")
    pages = relationship("ContractPage", back_populates="contract_file")


class ContractPage(Base):
    __tablename__ = "contract_pages"
    id = Column(Integer, primary_key=True, index=True)
    contract_file_id = Column(Integer, ForeignKey("contract_files.id"), nullable=False)
    page_number = Column(Integer)
    ocr_text = Column(Text)
    ocr_confidence = Column(Float)
    thumbnail_url = Column(String(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contract_file = relationship("ContractFile", back_populates="pages")


class ContractSLA(Base):
    __tablename__ = "contract_sla"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), unique=True, nullable=False)
    apr_percent = Column(Float)
    money_factor = Column(Float)
    term_months = Column(Integer)
    monthly_payment = Column(Float)
    down_payment = Column(Float)
    fees_total = Column(Float)
    residual_value = Column(Float)
    residual_percent_msrp = Column(Float)
    msrp = Column(Float)
    cap_cost = Column(Float)
    cap_cost_reduction = Column(Float)
    mileage_allowance_yr = Column(Integer)
    mileage_overage_fee = Column(Float)
    early_termination_fee = Column(Float)
    disposition_fee = Column(Float)
    purchase_option_price = Column(Float)
    insurance_requirements = Column(Text)
    maintenance_resp = Column(Text)
    warranty_summary = Column(Text)
    late_fee_policy = Column(Text)
    other_terms = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    contract = relationship("Contract", back_populates="sla")


class ExtractedClause(Base):
    __tablename__ = "extracted_clauses"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    clause_type = Column(String(100))
    page_number = Column(Integer)
    text_snippet = Column(Text)
    normalized_value = Column(JSON)
    red_flag_level = Column(String(20))
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="extracted_clauses")


class Extraction(Base):
    __tablename__ = "extractions"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    model_name = Column(String(100))
    prompt_version = Column(String(50))
    status = Column(String(30))
    details = Column(String(512))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    raw_output = Column(JSON)
    error_message = Column(Text)

    contract = relationship("Contract", back_populates="extractions")


class NegotiationThread(Base):
    __tablename__ = "negotiation_threads"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=True)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=True)
    channel = Column(String(50), default="chat")
    subject = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="negotiation_threads")
    contract = relationship("Contract", back_populates="negotiation_threads")
    messages = relationship("NegotiationMessage", back_populates="thread")


class NegotiationMessage(Base):
    __tablename__ = "negotiation_messages"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("negotiation_threads.id"), nullable=False)
    sender_role = Column(String(20))
    body = Column(Text)
    suggested_text = Column(Text)
    attachments = Column(JSON)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    thread = relationship("NegotiationThread", back_populates="messages")


class PriceRecommendation(Base):
    __tablename__ = "price_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    geo_postal = Column(String(20))
    msrp = Column(Float)
    fair_price_low = Column(Float)
    fair_price_high = Column(Float)
    basis = Column(String(200))
    methodology = Column(Text)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    vehicle = relationship("Vehicle", back_populates="price_recommendations")


class OfferComparison(Base):
    __tablename__ = "offer_comparisons"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    primary_contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    compared_contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    comparison_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IntegrationLog(Base):
    __tablename__ = "integration_logs"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    request_path = Column(String(512))
    request_params = Column(JSON)
    response_status = Column(Integer)
    response_ms = Column(Integer)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    error_message = Column(Text)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    entity_table = Column(String(100))
    entity_id = Column(Integer)
    action = Column(String(50))
    details = Column(JSON)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())


class Tagging(Base):
    __tablename__ = "tagging"
    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String(100))
    entity_table = Column(String(100))
    entity_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PriceSource(Base):
    __tablename__ = "price_sources"
    id = Column(Integer, primary_key=True, index=True)
    price_rec_id = Column(Integer, ForeignKey("price_recommendations.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    sample_size = Column(Integer)
    median_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    url = Column(String(512))
    raw = Column(JSON)