AutoLease — AI Car Lease Analysis Agent

Team Member: M. Saran
Branch: AI_CarAssistant-Saran
Project: AI-Powered Car Lease Analysis Platform

📌 Project Overview

AutoLease is an AI-powered full-stack web application that analyzes car lease agreements and helps users make smarter financial decisions.

Users can upload a lease document and instantly receive:

📊 Structured financial data
⚠️ Risk analysis
📝 Simple summaries
🤖 AI-powered answers
🚘 VIN verification
🧠 System Architecture
User uploads document (PDF / Image)
        ↓
   OCR Module (OCR / pdfplumber)
        ↓
   Data Extraction Module
        ↓
   AI Analysis (Gemini API)
        ↓
   Decision Logic (Risk Scoring)
        ↓
   VIN Verification (NHTSA API)
        ↓
   Structured Output + Chatbot

✨ Features

📄 Smart Document Upload
Supports PDF and Images
Extracts lease data automatically

🔍 OCR Extraction
Converts scanned documents → readable text
Works with low-quality images

🤖 AI Lease Analysis
Extracts key lease fields:
Monthly payment
Interest rate
Mileage limits
Fees

⚠️ Risk Detection
Identifies:
High interest rates
Hidden charges
Unfair clauses

📊 Lease Risk Score
Score from 0–100
Levels:
🟢 Low
🟡 Medium
🟠 High
🔴 Critical

📝 Plain Language Summary
Converts legal contract → easy English

💬 AI Chatbot
Ask questions like:
“What is my monthly payment?”
“Is this lease risky?”

🚘 VIN Verification (NHTSA API)
Extracts or accepts VIN
Verifies:
Manufacturer
Model
Year
Vehicle type

📈 Lease Insights Dashboard
Displays:
Extracted data
Risk score
AI insights

🛠️ Tech Stack
Backend
FastAPI — API framework
Python — Core logic
Gemini API — AI analysis
OCR + pdfplumber — Text extraction
NHTSA API — VIN verification
Frontend
HTML, CSS, JavaScript
Tools
Git & GitHub

📁 Project Structure
AutoLease/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── risk_scorer.py      # Risk calculation logic
│   ├── test_risk_scorer.py # Testing script
│   └── .env
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   ├── auth.html
│   ├── login.html
│   └── signup.html
│
└── README.md

🚀 How to Run

🔹 Backend Setup
cd backend
pip install fastapi uvicorn python-dotenv openai pypdf easyocr
python main.py

Backend runs at:
👉 http://127.0.0.1:8000

🔹 Frontend Setup
cd frontend
python -m http.server 8080

Frontend runs at:
👉 http://127.0.0.1:8080

---

## 📊 Module Breakdown

| Module | Technology | Purpose |
|--------|------------|---------|
| OCR | EasyOCR, PyPDF | Extract text |
| AI Analysis | Gemini API | Understand lease |
| Risk Scoring | Python Logic | Detect risks |
| VIN Verification | NHTSA API | Validate vehicle |
| Chatbot | Gemini API | Answer questions |
| Frontend | HTML, JS | UI |
| Backend | FastAPI | API |

---

## 🧪 Test Cases

| Module | Test | Expected Result |
|--------|------|-----------------|
| Upload | PDF lease | Data extracted |
| Upload | Image lease | OCR works |
| AI | Lease with payment | Payment extracted |
| AI | Lease with fees | Fees detected |
| Risk | High interest | Flag shown |
| VIN | Valid VIN | Vehicle details returned |
| Chatbot | "Monthly payment?" | Correct answer |
| Chatbot | "Is this risky?" | Risk explanation |

---

## 🔌 API Endpoints
📤 Upload Lease

POST /extract-lease/

💬 Ask Questions

POST /ask/

⚠️ Calculate Risk

POST /calculate-risk/

📝 Generate Summary

POST /generate-summary/

🚘 VIN Verification

GET /decode-vin/{vin}


🔮 Future Improvements
JWT Authentication
Cloud deployment (AWS/Vercel)
Advanced analytics dashboard
Multi-language support
Advanced VIN insights

👨‍💻 Developer
M. Saran

What I built:
This PR includes the complete implementation of an AI-powered car lease analysis system.

Modules Implemented:
✅ OCR Module — EasyOCR + PyPDF for document extraction  
✅ AI Analysis — Gemini API for lease understanding  
✅ Risk Scoring — Rule-based lease risk detection  
✅ VIN Verification — NHTSA API integration  
✅ AI Chatbot — Answers user queries  
✅ Frontend Dashboard — HTML, CSS, JavaScript  
✅ Backend API — FastAPI  

How to test:
1. Upload a lease document (PDF/Image)
2. Wait for analysis
3. View extracted data and risk score
4. Ask chatbot questions
5. Test VIN verification with a valid VIN
