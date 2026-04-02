# 🛡️ AutoGuard — AI-Powered Car Lease Analyzer

AutoGuard is a full-stack web application that helps consumers understand, review, and negotiate car lease contracts using AI. It extracts key SLA terms, computes a **Contract Fairness Score**, performs **VIN lookups**, and provides an **AI negotiation chatbot**.

---

## 📁 Project Structure

```
autoguard/
├── backend/               # FastAPI Python backend
│   ├── main.py            # App entry point
│   ├── database.py        # SQLite DB setup
│   ├── requirements.txt   # Python dependencies
│   ├── routers/           # API route handlers
│   │   ├── auth.py        # Login / Register
│   │   ├── contracts.py   # Upload & manage contracts
│   │   ├── extraction.py  # LLM SLA extraction
│   │   ├── vin.py         # VIN lookup
│   │   └── chat.py        # Negotiation chatbot
│   ├── models/            # SQLAlchemy DB models
│   │   └── models.py
│   ├── services/          # Business logic
│   │   ├── ocr_service.py
│   │   ├── llm_service.py
│   │   └── vin_service.py
│   └── utils/
│       └── auth_utils.py  # JWT helpers
│
├── frontend/              # React frontend
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/    # Reusable UI components
│       │   ├── Navbar.jsx
│       │   ├── UploadZone.jsx
│       │   ├── FairnessScore.jsx
│       │   ├── SLAGrid.jsx
│       │   ├── FlagsList.jsx
│       │   ├── VINLookup.jsx
│       │   └── ChatBot.jsx
│       ├── pages/         # Route pages
│       │   ├── LoginPage.jsx
│       │   └── DashboardPage.jsx
│       ├── services/      # API calls
│       │   └── api.js
│       └── hooks/
│           └── useAuth.js
│
├── database/
│   └── schema.sql         # DB schema reference
│
├── .env.example           # Environment variables template
├── .gitignore
└── docker-compose.yml     # Optional Docker setup
```

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/autoguard.git
cd autoguard
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 4. Run the Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```
Backend runs at: http://localhost:8000  
API Docs at: http://localhost:8000/docs

### 5. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: http://localhost:5173

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude AI API key (get from console.anthropic.com) |
| `SECRET_KEY` | JWT secret key (any random string) |
| `DATABASE_URL` | SQLite path (default: `./autoguard.db`) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Frontend | React + Vite |
| Database | SQLite (via SQLAlchemy) |
| AI/LLM | Claude (Anthropic API) |
| OCR | pdfplumber + pytesseract |
| VIN Lookup | NHTSA Public API |
| Auth | JWT (python-jose) |
| Styling | Plain CSS (no framework) |
