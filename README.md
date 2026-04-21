# 🚗 Car Lease Agreement Analyzer

> AI-powered full-stack web application that analyzes car lease and loan agreements — built for Infosys Springboard AI Car Assistant Project.

**Developer:** Ayisha Parli | **Branch:** `AI_carAssistant-Ayisha`

---

## 📌 Overview

Upload any car lease or loan contract and instantly receive a structured analysis including key financial terms, risk highlights, negotiation suggestions, and an interactive chatbot.

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| 📄 | Smart Document Upload | Accepts PDF, scanned PDF, images (JPG/PNG), and plain text |
| 🔍 | OCR Extraction | Extracts raw text from any document format |
| 🤖 | AI Contract Analysis | LLM extracts all key SLA fields |
| ⚠️ | Risk Detection | Identifies red flags and unusual clauses |
| 📊 | Fairness Score | 0–100 score showing how fair the deal is |
| 💬 | Plain Language Summary | Simple explanation anyone can understand |
| 🔧 | Negotiation Suggestions | AI-powered tips to get better terms |
| 🚗 | VIN Lookup | Verify vehicle details and check recall history |
| 💡 | Interactive Chatbot | Ask questions like "Is this interest rate high?" |
| 📈 | Deal Comparison | Compare two contracts side by side |

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — Python web framework
- **Gemini / Groq** — LLM integration
- **PyMuPDF + Tesseract** — OCR for text extraction
- **SQLAlchemy + PostgreSQL** — Database
- **NHTSA Public API** — VIN verification

### Frontend
- **React 18 + TypeScript** — UI framework
- **Tailwind CSS** — Styling
- **Zustand** — State management
- **React Query** — API data fetching

---

## 📁 Project Structure
AI_CarAssistant/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # Auth, Contracts, VIN, Negotiation
│   │   ├── core/            # Config, Database, Security
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # OCR, LLM, VIN services
│   │   └── main.py          # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # UI pages
│   │   ├── components/      # Reusable components
│   │   ├── api/             # API client
│   │   ├── store/           # State management
│   │   └── types/           # TypeScript types
│   └── package.json
└── README.md
---

## 🚀 Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=your_postgresql_url
LLM_API_KEY=your_llm_api_key
SECRET_KEY=your_secret_key
```

---

## 🧠 System Architecture
User Uploads Document (PDF / Scanned PDF / Image / Text)
↓
OCR Module (PyMuPDF + Tesseract)
↓
Contract Understanding Module (LLM Integration)
↓
Decision Logic (Risk Detection + Fairness Score)
↓
VIN Verification (NHTSA Public API)
↓
Structured Output + Interactive Chatbot
---

## 📊 Module Breakdown

| Module | Technology | Purpose |
|---|---|---|
| OCR | PyMuPDF + Tesseract | Extract text from documents |
| LLM | Gemini / Groq | Understand contract content |
| Decision Logic | Python + LLM | Detect risks & fairness scoring |
| VIN Verification | NHTSA API | Validate vehicle information |
| Chatbot | LLM + FastAPI | Answer contract questions |
| Frontend | React + TypeScript | User interface |
| Database | PostgreSQL | Store contracts & analysis |

---

## 🧪 Test Cases

| Module | Input | Expected Result |
|---|---|---|
| Upload | PDF contract | Text extracted successfully |
| Upload | Scanned image | OCR extracts text |
| LLM | Contract with APR | APR extracted correctly |
| LLM | Contract with VIN | VIN identified and verified |
| Risk | High APR contract | Red flag shown |
| VIN | Valid 17-char VIN | Vehicle details fetched |
| Chatbot | "What is my monthly payment?" | Correct amount returned |
| Chatbot | "Is this interest rate high?" | AI comparison given |

---

## ✅ Modules Implemented

- [x] OCR Module — PyMuPDF + Tesseract for PDF/image/text extraction
- [x] Contract Understanding Module — LLM Integration
- [x] Decision Logic Module — Risk detection, fairness scoring
- [x] VIN Verification — NHTSA public API integration
- [x] Interactive Chatbot — Answers contract questions on results page
- [x] Full Frontend — React + TypeScript + Tailwind CSS
- [x] REST API — FastAPI with JWT authentication
- [x] Database — PostgreSQL

---

## 👩‍💻 Developer

**Ayisha Parli**  
Infosys Springboard AI Program  
Branch: `AI_carAssistant-Ayisha`
