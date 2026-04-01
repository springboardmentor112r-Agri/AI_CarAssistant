# 🚗 Car Lease Agreement Analyzer — AI Agent

**Team Member:** Sonalee Shaktula  
**Branch:** AI_carAssistant-Sonalee  
**Project:** Infosys Springboard — AI Car Assistant  

---

## 🚀 Live Deployment
- **Web Application:** [https://car-lease-frontend.onrender.com](https://car-lease-frontend.onrender.com)
- **API Documentation:** [https://car-lease-.onrender.com/docs](https://car-lease-.onrender.com/docs)

---

## 🧪 Quick Test Guide (For Reviewers)
To test the AI logic on the frontend, follow these 3 simple steps:

1. **Sign Up:** Create a test account (e.g., `test@gmail.com`). 
   *Note: If the site is "sleeping," the first load may take 1 minute.*
2. **Upload a Test Case:** You don't need a real PDF. Simply upload a `.txt` file with this text:
   > "2024 Mazda CX-5. Monthly: $700. Term: 36 mo. APR: 19%. MSRP: $32,000."
3. **Verify AI Results:** - Check if the AI correctly flags the **19% APR** as a **"High Risk / Red Flag"**.
   - Open the **Chatbot** and ask: *"Is this a good deal for this car?"*
   - Go to the **VIN Tab** and enter `1GCVK64C0FZ123456` to see live vehicle data.

---

## 📌 Project Overview

An AI-powered full-stack web application that analyzes car lease and loan agreements. Users can upload a contract document and instantly receive a structured analysis including key financial terms, risk highlights, negotiation suggestions, and an interactive chatbot.

---

## 🧠 System Architecture
```
User uploads document (PDF / Scanned PDF / Image / Text)
        ↓
   OCR Module (PyMuPDF + Tesseract)
        ↓
   Contract Understanding Module (Google Gemini AI)
        ↓
   Decision Logic Module (Risk Detection + Fairness Score)
        ↓
   VIN Verification (NHTSA Public API)
        ↓
   Structured Output + Interactive Chatbot
```

---

## ✨ Features

- 📄 **Smart Document Upload** — Accepts PDF, scanned PDF, images (JPG/PNG), and plain text
- 🔍 **OCR Extraction** — Extracts raw text from any document format
- 🤖 **AI Contract Analysis** — Gemini AI extracts all key SLA fields
- ⚠️ **Risk Detection** — Identifies red flags and unusual clauses
- 📊 **Fairness Score** — 0-100 score showing how fair the deal is
- 💬 **Plain Language Summary** — Simple explanation anyone can understand
- 🔧 **Negotiation Suggestions** — AI-powered tips to get better terms
- 🚗 **VIN Lookup** — Verify vehicle details and check recall history
- 💡 **Interactive Chatbot** — Ask questions like "Is this interest rate high?"
- 📈 **Deal Comparison** — Compare two contracts side by side

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — Python web framework
- **Google Gemini 2.5 Flash** — LLM for contract understanding
- **PyMuPDF + Tesseract** — OCR for text extraction
- **SQLAlchemy + PostgreSQL (Neon)** — Database
- **NHTSA Public API** — VIN verification

### Frontend
- **React 18 + TypeScript** — UI framework
- **Tailwind CSS** — Styling
- **Zustand** — State management
- **React Query** — API data fetching

---

## 📁 Project Structure
```
AI_CarAssistant/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # Auth, Contracts, VIN, Negotiation, Price
│   │   ├── core/            # Config, Database, Security
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # OCR, LLM, VIN, Price services
│   │   └── main.py          # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # All UI pages
│   │   ├── components/      # Reusable components
│   │   ├── api/             # API client
│   │   ├── store/           # Auth state
│   │   └── types/           # TypeScript types
│   └── package.json
└── README.md
```

---

## 🚀 How to Run

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

### Environment Variables (backend/.env)
```
DATABASE_URL=your_neon_postgresql_url
GOOGLE_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
```

---

## 📊 Module Breakdown

| Module | Technology | Purpose |
|--------|-----------|---------|
| OCR | PyMuPDF + Tesseract | Extract text from documents |
| LLM | Google Gemini 2.5 Flash | Understand contract content |
| Decision Logic | Python + Gemini | Detect risks and suggest negotiations |
| VIN Verification | NHTSA API | Validate vehicle information |
| Chatbot | Gemini + FastAPI | Answer user questions about contract |
| Frontend | React + TypeScript | User interface |
| Database | PostgreSQL (Neon) | Store contracts and analysis |

---

## 🧪 Test Cases

| Module | Test | Expected Result |
|--------|------|----------------|
| Upload | PDF contract | Text extracted successfully |
| Upload | Scanned image | OCR extracts text |
| Upload | Plain text file | Text read directly |
| LLM | Contract with APR | APR extracted correctly |
| LLM | Contract with VIN | VIN identified and verified |
| Risk | High APR contract | Red flag shown |
| VIN | Valid 17-char VIN | Vehicle details fetched |
| Chatbot | "What is my monthly payment?" | Correct amount returned |
| Chatbot | "Is this interest rate high?" | AI comparison given |

---

## 👩‍💻 Developer

**Sonalee Shaktula**  
Infosys Springboard AI Program  
Branch: `AI_carAssistant-Sonalee`
```

---

## Pull Request Description — paste this when creating PR:
```
## 🚗 Car Lease Agreement Analyzer — Complete Implementation

### What I built:
This PR contains the complete implementation of the Car Lease Agreement Analyzer AI Agent.

### Modules Implemented:
- ✅ OCR Module — PyMuPDF + Tesseract for PDF/image/text extraction
- ✅ Contract Understanding Module — Google Gemini 2.5 Flash
- ✅ Decision Logic Module — Risk detection, fairness scoring
- ✅ VIN Verification — NHTSA public API integration
- ✅ Interactive Chatbot — On results page, answers contract questions
- ✅ Full Frontend — React + TypeScript + Tailwind CSS
- ✅ REST API — FastAPI with JWT authentication
- ✅ Database — PostgreSQL via Neon

### How to test:
1. Upload the sample Chevrolet lease PDF
2. Wait ~30 seconds for AI analysis
3. Review extracted fields, red flags, and fairness score
4. Ask chatbot "Is this interest rate high?"
5. Try VIN lookup with any 17-character VIN
