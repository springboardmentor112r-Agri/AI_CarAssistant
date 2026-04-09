from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.database import engine, Base
from app.models import *  # noqa: ensure all models are imported for table creation

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Car Lease/Loan Contract Review AI",
    description="AI-powered contract analysis, negotiation assistant, and vehicle price estimation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "car-lease-ai-backend"}