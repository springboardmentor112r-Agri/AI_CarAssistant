
# AI-Negotiation-for-car-lease-or-loan

## Prerequisites
  sudo apt install poppler-utils -y
  # uv must be already installed

## Database Setup (Neon — Free)
  1. Go to https://neon.tech
  2. Sign up and create project: car-contract-ai
  3. Select region: ap-south-1 (Mumbai) — closest to India
  4. Copy connection string
  5. Add to backend/.env:
     DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/car_contract_db?sslmode=require

## Backend
  cd backend
  uv venv .venv
  source .venv/bin/activate
  uv pip install -r requirements.txt
  cp .env.example .env
  # Edit .env with all keys
  uv run alembic upgrade head
  uv run uvicorn main:app --reload --port 8000

## Frontend (new terminal)
  cd frontend
  npm install
  cp .env.example .env
  npm run dev

## URLs
  Frontend: https://ai-negotiation-for-car-lease-or-loa.vercel.app/ 
  Backend:https://ai-negotiation-for-car-lease-or-loan-2.onrender.com

