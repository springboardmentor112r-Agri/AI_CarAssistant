from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import Base, engine
from routers import auth, contracts, extraction, vin, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all DB tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AutoGuard API",
    description="AI-Powered Car Lease Contract Review & Negotiation Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/api/auth",       tags=["Auth"])
app.include_router(contracts.router,   prefix="/api/contracts",  tags=["Contracts"])
app.include_router(extraction.router,  prefix="/api/extraction", tags=["Extraction"])
app.include_router(vin.router,         prefix="/api/vin",        tags=["VIN"])
app.include_router(chat.router,        prefix="/api/chat",       tags=["Chat"])


@app.get("/")
def root():
    return {"message": "AutoGuard API is running", "docs": "/docs"}
