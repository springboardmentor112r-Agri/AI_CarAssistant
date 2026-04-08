from fastapi import FastAPI, Depends, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager
from typing import Optional
import uuid
import os
import asyncio

from app.database import engine, Base, get_db
from app.database import engine, Base, get_db
from app import models, schemas, schemas_chat
from app.services.document_parser import extract_text_from_pdf
from app.services.llm_extractor import extract_sla_from_text
from app.services.vin_lookup import fetch_vin_details
from app.services.chatbot import generate_negotiation_reply

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (For local dev SQLite/simple cases)
    # In production, use Alembic migrations instead
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup on shutdown

os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="Car Lease/Loan Contract Review App API", lifespan=lifespan)

# Setup CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Car Lease/Loan Contract Review API"}

@app.post("/api/contracts/upload", response_model=schemas.ContractResponse)
async def upload_contract(
    user_id: str, # temporary placeholder until auth is implemented
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Save file locally for now
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    # Create dummy user if missing for local test
    from sqlalchemy import select
    from app.models import User
    import uuid
    
    result = await db.execute(select(User).limit(1))
    user = result.scalars().first()
    if not user:
        user = User(email="test@user.com", password_hash="hash")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    new_contract = models.Contract(
        user_id=user.id,
        file_url=file_location,
        status=models.ContractStatus.PENDING
    )
    db.add(new_contract)
    await db.commit()
    await db.refresh(new_contract)
    
    # Queue background task to extract text and update status
    background_tasks.add_task(process_contract_background, new_contract.id, file_location)
    
    return new_contract

@app.get("/api/contracts/{contract_id}", response_model=dict)
async def get_contract(contract_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Fetches the contract and its extracted SLA components.
    """
    from sqlalchemy import select
    
    # Eager load the related ExtractedSLA and Vehicle to avoid detached session issues
    stmt = select(models.Contract).options(
        selectinload(models.Contract.extracted_sla),
        selectinload(models.Contract.vehicle)
    ).where(models.Contract.id == contract_id)
    result = await db.execute(stmt)
    contract = result.scalars().first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
        
    response = {
        "id": contract.id,
        "status": contract.status,
        "created_at": contract.created_at,
        "file_url": contract.file_url,
    }

    if contract.vehicle:
        response["vehicle"] = {
            "make": contract.vehicle.make,
            "model": contract.vehicle.model,
            "year": contract.vehicle.year,
            "vin": contract.vehicle.vin,
        }
    
    if contract.extracted_sla:
        response["sla"] = {
            "apr": contract.extracted_sla.apr,
            "lease_term_months": contract.extracted_sla.lease_term_months,
            "monthly_payment": contract.extracted_sla.monthly_payment,
            "down_payment": contract.extracted_sla.down_payment,
            "residual_value": contract.extracted_sla.residual_value,
            "mileage_allowance": contract.extracted_sla.mileage_allowance,
            "overage_charge_per_mile": contract.extracted_sla.overage_charge_per_mile,
            "buyout_price": contract.extracted_sla.buyout_price,
            "fairness_score": contract.extracted_sla.fairness_score,
            "red_flags": contract.extracted_sla.red_flags,
        }
    
    return response

@app.get("/api/vehicles/vin/{vin}", response_model=dict)
async def get_vehicle_by_vin(vin: str, contract_id: Optional[uuid.UUID] = None, db: AsyncSession = Depends(get_db)):
    """
    Fetches VIN details and stores them in DB if contract_id is provided.
    """
    vehicle_data = await fetch_vin_details(vin)
    
    if not vehicle_data:
        raise HTTPException(status_code=404, detail="Vehicle not found or VIN invalid")
        
    if contract_id:
        # Save or update vehicle details tied to contract
        from sqlalchemy import select
        stmt = select(models.Vehicle).where(models.Vehicle.contract_id == contract_id)
        result = await db.execute(stmt)
        vehicle = result.scalars().first()
        
        if not vehicle:
            vehicle = models.Vehicle(
                contract_id=contract_id,
                vin=vin,
                make=vehicle_data.get("make"),
                model=vehicle_data.get("model"),
                year=vehicle_data.get("year"),
            )
            db.add(vehicle)
        else:
            vehicle.vin = vin
            vehicle.make = vehicle_data.get("make")
            vehicle.model = vehicle_data.get("model")
            vehicle.year = vehicle_data.get("year")
            
        await db.commit()
        await db.refresh(vehicle)
        
        return {
            "id": vehicle.id,
            "vin": vehicle.vin,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year
        }
    
    # Return directly if no contract to bind
    return vehicle_data

@app.post("/api/contracts/{contract_id}/chat", response_model=schemas_chat.MessageResponse)
async def chat_with_assistant(contract_id: uuid.UUID, message: schemas_chat.MessageCreate, db: AsyncSession = Depends(get_db)):
    """
    Endpoint for users to ask questions about their contract.
    """
    from sqlalchemy import select
    
    # Verify contract exists and get SLA summary
    stmt = select(models.Contract).options(selectinload(models.Contract.extracted_sla)).where(models.Contract.id == contract_id)
    result = await db.execute(stmt)
    contract = result.scalars().first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
        
    user_id = contract.user_id # Using the contract's user as the owner
    
    # Get or create conversation
    conv_stmt = select(models.Conversation).where(models.Conversation.contract_id == contract_id)
    conv_result = await db.execute(conv_stmt)
    conversation = conv_result.scalars().first()
    
    if not conversation:
        conversation = models.Conversation(user_id=user_id, contract_id=contract_id)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
    # Save User Message
    user_msg = models.Message(
        conversation_id=conversation.id,
        role=models.RoleEnum.USER,
        content=message.content
    )
    db.add(user_msg)
    await db.commit()
    
    # Fetch History
    hist_stmt = select(models.Message).where(models.Message.conversation_id == conversation.id).order_by(models.Message.timestamp.asc())
    hist_result = await db.execute(hist_stmt)
    history = [{"role": msg.role, "content": msg.content} for msg in hist_result.scalars().all()][:-1] # exclude current
    
    # Prepare Summary Context
    summary = {}
    if contract.extracted_sla:
        summary = {
            "apr": contract.extracted_sla.apr,
            "monthly_payment": contract.extracted_sla.monthly_payment,
            "lease_term_months": contract.extracted_sla.lease_term_months,
            "residual_value": contract.extracted_sla.residual_value,
            "mileage_allowance": contract.extracted_sla.mileage_allowance,
            "red_flags": contract.extracted_sla.red_flags or [],
            "fairness_score": contract.extracted_sla.fairness_score
        }
        
    # Generate Reply
    reply_content = await generate_negotiation_reply(summary, history, message.content)
    
    # Save Assistant Message
    assistant_msg = models.Message(
        conversation_id=conversation.id,
        role=models.RoleEnum.ASSISTANT,
        content=reply_content
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    
    return assistant_msg

async def process_contract_background(contract_id: uuid.UUID, file_path: str):
    """
    Background job to parse the PDF, extract raw text, and save.
    In the next milestone, this will also trigger the LLM to structure SLAs.
    """
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        contract = await session.get(models.Contract, contract_id)
        if not contract:
            return

        try:
            contract.status = models.ContractStatus.EXTRACTING
            await session.commit()
            
            # Step 1: Basic text extraction (OCR/PyMuPDF)
            # This handles running the synchronous PyMuPDF call via asyncio for safety
            raw_text = await extract_text_from_pdf(file_path)
            contract.raw_text = raw_text
            
            # Step 2: Use LLM to extract structured SLAs
            sla_data = await extract_sla_from_text(raw_text)
            
            # Save extracted SLA to database
            extracted_sla = models.ExtractedSLA(
                contract_id=contract.id,
                apr=sla_data.get("apr"),
                lease_term_months=sla_data.get("lease_term_months"),
                monthly_payment=sla_data.get("monthly_payment"),
                down_payment=sla_data.get("down_payment"),
                residual_value=sla_data.get("residual_value"),
                mileage_allowance=sla_data.get("mileage_allowance"),
                overage_charge_per_mile=sla_data.get("overage_charge_per_mile"),
                early_termination_clause=sla_data.get("early_termination_clause"),
                buyout_price=sla_data.get("buyout_price"),
                fairness_score=sla_data.get("fairness_score"),
                red_flags=sla_data.get("red_flags")
            )
            session.add(extracted_sla)
            
            # Step 3: Use LLM-extracted vehicle data to seed the Vehicle table
            if sla_data.get("vehicle_make") or sla_data.get("vehicle_model"):
                vehicle = models.Vehicle(
                    contract_id=contract.id,
                    make=sla_data.get("vehicle_make"),
                    model=sla_data.get("vehicle_model"),
                    year=sla_data.get("vehicle_year")
                )
                session.add(vehicle)

            # Marking as complete
            contract.status = models.ContractStatus.COMPLETED
            await session.commit()
            
        except Exception as e:
            contract.status = models.ContractStatus.FAILED
            await session.commit()
            print(f"Failed to process contract {contract_id}: {e}")
