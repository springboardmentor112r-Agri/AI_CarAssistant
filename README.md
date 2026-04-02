# 🚗 Car Lease Agreement Analyzer

An AI-Powered System for Automated Car Lease Contract Analysis and Intelligent Negotiation Support

Built as part of **Infosys Springboard AI Domain Internship**

---

## 📌 Problem Statement

When a person goes to buy or lease a car, the dealer provides a contract with many pages of complex legal language. Most people do not understand terms like APR, money factor, residual value, cap cost, disposition fee or early termination charges. They sign the contract without fully understanding what they are agreeing to. This leads to:

- **Hidden fees** — Unexpected charges like mileage overage fees and disposition fees that people never notice
- **Inadequate transparency** — Critical clauses like arbitration terms and default conditions buried in dense legal text
- **Ambiguous language** — Complex legal jargon that a common person cannot understand
- **Poor financial decisions** — Signing unfair contracts without knowing the actual risks and obligations

---

## ✅ Our Approach

Our system solves this problem by allowing users to upload any car lease or loan contract document and receive a complete AI-powered analysis within 30 seconds.

The approach follows a 6-step pipeline:

1. **Document Upload** — User uploads PDF, scanned image or text file through the web application
2. **OCR Processing** — PyMuPDF extracts text from digital PDFs, Tesseract OCR handles scanned documents and images
3. **AI Extraction** — Google Gemini 2.5 Flash reads the raw text and extracts 25+ structured fields from the contract
4. **Decision Logic** — System calculates fairness score from 0 to 100, identifies red flags and generates negotiation suggestions
5. **VIN Verification** — NHTSA government API validates vehicle details and checks active safety recalls
6. **Results and Chatbot** — Complete analysis displayed on dashboard with AI chatbot ready for follow-up questions

---
## 🚀 Live Deployment & Demo

The application is fully containerized and deployed. You can interact with the AI assistant through the live links below.

### 🌐 Application Status
![Frontend Status](https://img.shields.io/badge/Frontend-Live-success?style=for-the-badge&logo=react&logoColor=white)
![Backend Status](https://img.shields.io/badge/Backend-Active-blue?style=for-the-badge&logo=fastapi&logoColor=white)
![Database](https://img.shields.io/badge/Database-Neon_Postgres-00e599?style=for-the-badge&logo=postgresql&logoColor=white)

### 🔗 Access Links
| Component | Technology Stack | Access Link |
| :--- | :--- | :--- |
| **User Interface** | React + Vite + Tailwind | [Open Web App ↗️](https://ai-car-frontend.onrender.com) |
| **API Service** | FastAPI + SQLAlchemy | [Check API Health ↗️](https://ai-car-backend-new.onrender.com/health) |

### 📺 Video Walkthrough
<details>
  <summary><b>▶️ Click here to watch the 3-minute Feature Demo</b></summary>
  <br>
  
   [https://github.com/user-attachments/assets/80ce8808-f3aa-48c2-bf81-5626f39bf639]


  
  *The video demonstrates: User Authentication, PDF Upload, and AI Contract Analysis.*
</details>

> [!IMPORTANT]
> **Cold Start Warning:** This project is hosted on Render's Free Tier. If the app hasn't been used recently, the server "spins down." Please allow **30-60 seconds** for the first request to process while the server wakes up.

---

## 🌟 Key Features

| Feature | Description |
|---|---|
| 📄 Smart OCR | Reads PDF, scanned documents, images and text files using PyMuPDF and Tesseract |
| 🤖 AI Contract Analysis | Extracts 25+ fields using Google Gemini 2.5 Flash AI model |
| 📊 Fairness Score (0-100) | AI calculates score based on APR reasonableness, payment fairness and penalty evaluation |
| 🚩 Red Flag Detection | Automatically identifies risky and unfair clauses in the contract |
| 💬 AI Negotiation Chatbot | Answers questions with pointwise explanations and ready-to-send dealer messages |
| 🚗 VIN Verification | Validates vehicle details and checks safety recalls using NHTSA government API |
| ⚖️ Deal Comparison | Compare two contracts side by side with detailed AI analysis and savings calculation |
| 🔐 Secure Authentication | JWT based user authentication with bcrypt password hashing |
| 📝 Plain Language Summary | AI generates a simple 3-4 sentence summary anyone can understand |
| 💡 Negotiation Suggestions | AI provides specific tips to negotiate better terms with the dealer |

---

## 🛠️ Tech Stack

### Frontend
- **React** with TypeScript — UI framework
- **Tailwind CSS** — Styling
- **TanStack Query** — API state management
- **Vite** — Build tool

### Backend
- **FastAPI** (Python) — REST API framework
- **SQLAlchemy** — ORM for database operations
- **JWT** — JSON Web Token authentication
- **bcrypt** — Password hashing and security

### AI and ML
- **Google Gemini 2.5 Flash** — Contract analysis and AI chatbot
- **PyMuPDF** — Digital PDF text extraction
- **Tesseract OCR** — Scanned document and image processing
- **JSON Structured Output** — Structured data extraction from AI

### Database and APIs
- **PostgreSQL on Neon** — Cloud serverless database
- **NHTSA VIN API** — Government vehicle verification API
- **GitHub Codespaces** — Cloud development environment
- **Git** — Version control

---

## 📁 Project Structure

```
AI_CarAssistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── auth.py          # Authentication endpoints
│   │   │       ├── contracts.py     # Contract upload and management
│   │   │       ├── negotiation.py   # AI Chatbot endpoints
│   │   │       ├── price.py         # Deal comparison endpoints
│   │   │       └── vin.py           # VIN verification endpoints
│   │   ├── core/
│   │   │   ├── config.py            # Environment configuration
│   │   │   ├── database.py          # Database connection with pool
│   │   │   └── security.py          # JWT and bcrypt security
│   │   ├── models/                  # SQLAlchemy database models
│   │   ├── services/
│   │   │   ├── llm_service.py       # Google Gemini AI integration
│   │   │   └── ocr_service.py       # OCR text extraction service
│   │   └── main.py                  # FastAPI application entry point
│   ├── requirements.txt             # Python dependencies
│   └── .env                         # Environment variables (not committed to git)
├── frontend/
│   ├── src/
│   │   ├── api/                     # API client and endpoint functions
│   │   ├── components/              # Reusable UI components
│   │   ├── pages/                   # Application pages
│   │   │   ├── LandingPage.tsx      # Home landing page
│   │   │   ├── AuthPage.tsx         # Login and register page
│   │   │   ├── Dashboard.tsx        # Main dashboard
│   │   │   ├── ContractsPage.tsx    # All contracts list
│   │   │   ├── ContractDetailPage.tsx # Contract analysis detail
│   │   │   ├── NegotiatePage.tsx    # AI negotiation assistant
│   │   │   ├── ComparePage.tsx      # Deal comparison page
│   │   │   ├── VINPage.tsx          # VIN verification page
│   │   │   └── UploadPage.tsx       # Contract upload page
│   │   ├── store/                   # Zustand authentication store
│   │   └── types/                   # TypeScript type definitions
│   └── package.json
└── README.md
```

---

## 🚀 Steps to Run the Project

### Prerequisites
- Python 3.12 or higher
- Node.js 18 or higher
- PostgreSQL database (Neon recommended)
- Google Gemini API key from aistudio.google.com

### Step 1 — Clone the Repository
```bash
git clone https://github.com/springboardmentor112r-Agri/AI_CarAssistant.git
cd AI_CarAssistant
git checkout AI_CarAssistant--Yaghna-sri
```

### Step 2 — Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
pip uninstall bcrypt -y
pip install bcrypt==4.0.1
```

### Step 3 — Create Environment File
Create a `.env` file inside the `backend/` folder:
```
DATABASE_URL=your_neon_postgresql_connection_string
GOOGLE_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Step 4 — Create Database Tables
```bash
python -c "
from app.core.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('Tables created successfully!')
"
```

### Step 5 — Run Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6 — Install Frontend Dependencies (New Terminal)
```bash
cd frontend
npm install
```

### Step 7 — Configure Frontend API URL
```bash
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local
```

### Step 8 — Run Frontend
```bash
npm run dev
```

### Step 9 — Access the Application
- **Frontend:** `http://localhost:5173`
- **Backend API Docs:** `http://localhost:8000/docs`

> **Note:** If running on GitHub Codespaces replace localhost with your Codespace URL and make ports 8000 and 5173 public in the PORTS tab.

---

## 🔄 Complete Workflow

```
User opens the website
        ↓
User registers or logs in securely
        ↓
User uploads contract (PDF / Scanned Image / TXT)
        ↓
OCR Module extracts text from document
(PyMuPDF for digital PDFs, Tesseract for scanned documents)
        ↓
Google Gemini 2.5 Flash analyzes the raw text
(Extracts 25+ structured fields as JSON)
        ↓
Decision Logic Module processes extracted data
(Calculates Fairness Score + Identifies Red Flags + Generates Negotiation Points)
        ↓
VIN Verification via NHTSA Government API
(Validates vehicle details and checks safety recalls if VIN found)
        ↓
Complete Results displayed on Dashboard
(Fairness Score + Red Flags + Negotiation Suggestions + Plain Language Summary)
        ↓
AI Chatbot available for any user questions
(Powered by Google Gemini 2.5 Flash)
        ↓
Deal Comparison available
(Compare two contracts side by side with winner and savings amount)
```

---

## 📊 Database Schema

| Table | Description |
|---|---|
| users | Stores user accounts and hashed passwords |
| contracts | Stores uploaded contract metadata and processing status |
| contract_files | Stores uploaded file paths and MIME type details |
| contract_sla | Stores all 25+ extracted contract fields |
| extracted_clauses | Stores identified red flags and risky clauses |
| negotiation_threads | Stores AI chatbot conversation threads |
| negotiation_messages | Stores individual chatbot messages and suggested dealer responses |
| offer_comparisons | Stores deal comparison results and AI analysis |

---

## 🔐 Security Features

- JWT token based user authentication
- bcrypt password hashing with salt
- Environment variables for all sensitive data
- .env file excluded from git tracking via .gitignore
- SSL required database connections via Neon
- CORS protection configured on all API endpoints
- Cascade delete for clean data removal

---

## 📈 Future Scope

- Mobile application deployment for iOS and Android
- Multi-language contract support for regional languages
- Integration with car dealership CRM systems
- Real-time market price benchmarking
- Expansion to real estate and insurance contract analysis
- Email notifications for contract expiry and renewal reminders

---

## 👩‍💻 Developed By

**Yaghna sri**  
AI Domain Internship | Infosys Springboard 2025

Built with  using FastAPI · React · Google Gemini AI · PostgreSQL · NHTSA API
