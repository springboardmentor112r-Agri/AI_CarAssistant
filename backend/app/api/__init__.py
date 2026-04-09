from fastapi import APIRouter
from app.api.routes import auth, contracts, vin, negotiation, price

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(contracts.router)
api_router.include_router(vin.router)
api_router.include_router(negotiation.router)
api_router.include_router(price.router)