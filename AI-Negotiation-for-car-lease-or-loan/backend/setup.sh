#!/bin/bash
set -e
echo "=== Car Contract AI — Backend Setup ==="

echo "Step 1: Creating uv virtual environment..."
cd backend
uv venv .venv

echo "Step 2: Activating environment..."
source .venv/bin/activate

echo "Step 3: Installing dependencies..."
uv pip install -r requirements.txt

echo "Step 4: Copying env file..."
cp .env.example .env
echo ">>> IMPORTANT: Edit backend/.env with your Neon DATABASE_URL and API keys"

echo "Step 5: Install system dependency for PDF processing..."
sudo apt install poppler-utils -y

echo ""
echo "=== Setup complete ==="
echo "After editing .env run:"
echo "  uv run alembic upgrade head"
echo "  uv run uvicorn main:app --reload --port 8000"
