# 🚀 AutoGuard — Local Setup Guide

Follow these steps exactly to run AutoGuard on your local machine.

---

## Step 1 — Install Prerequisites

Make sure you have these installed:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ | https://python.org |
| Node.js | 18+   | https://nodejs.org |
| Tesseract OCR | Latest | See below |

### Install Tesseract OCR

**Windows:**
```
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
Add to PATH: C:\Program Files\Tesseract-OCR
```

**Mac:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

---

## Step 2 — Get the Code

```bash
git clone https://github.com/YOUR_USERNAME/autoguard.git
cd autoguard
```

Or download and unzip the project folder.

---

## Step 3 — Get Your Anthropic API Key

1. Go to https://console.anthropic.com
2. Sign in or create a free account
3. Go to **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-...`)

---

## Step 4 — Configure Environment

```bash
# From the root autoguard/ folder:
cp .env.example .env
```

Open `.env` in any text editor and fill in:

```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
SECRET_KEY=any-long-random-string-you-choose
DATABASE_URL=sqlite:///./autoguard.db
```

---

## Step 5 — Set Up the Backend

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

---

## Step 6 — Run the Backend

```bash
# Still inside backend/ with venv activated:
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Test it: open http://localhost:8000 in your browser → should show `{"message": "AutoGuard API is running"}`

API docs: http://localhost:8000/docs

---

## Step 7 — Set Up the Frontend

Open a **new terminal** window (keep the backend running):

```bash
cd frontend
npm install
```

---

## Step 8 — Run the Frontend

```bash
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

Open http://localhost:5173 in your browser 🎉

---

## ✅ Everything Running?

| Service | URL | Status |
|---------|-----|--------|
| Frontend | http://localhost:5173 | React app |
| Backend  | http://localhost:8000 | FastAPI    |
| API Docs | http://localhost:8000/docs | Swagger UI |

---

## Common Issues & Fixes

### ❌ `pytesseract.pytesseract.TesseractNotFoundError`
Tesseract is not installed or not in PATH.
- **Windows**: Re-run Tesseract installer, ensure "Add to PATH" is checked.
- **Mac**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

### ❌ `ModuleNotFoundError: No module named 'xxx'`
Your virtual environment is not activated.
```bash
# Windows:
backend\venv\Scripts\activate
# Mac/Linux:
source backend/venv/bin/activate
```

### ❌ `ANTHROPIC_API_KEY` error
Make sure `.env` file exists in the `backend/` folder (not `.env.example`), and the key is correct.

### ❌ Frontend shows "Request failed" on login
Make sure the backend is running on port 8000. The Vite proxy forwards `/api` calls to `http://localhost:8000`.

### ❌ `npm install` fails
Make sure Node.js 18+ is installed: `node --version`

---

## Pushing to GitHub

```bash
cd autoguard

# Initialize git
git init
git add .
git commit -m "Initial commit: AutoGuard Car Lease AI Assistant"

# Create a repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/autoguard.git
git branch -M main
git push -u origin main
```

> ⚠️ Never commit your `.env` file — it is already in `.gitignore`.
