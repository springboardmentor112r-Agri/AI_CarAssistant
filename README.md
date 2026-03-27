# 🚗 AI Car Contract Analyzer

**Branch:** AI_CarAssistant-AnushkaBhatt
**Project:** Infosys Springboard — AI Car Assistant

---

## 📌 Overview

This is a web application that analyzes car lease or loan contracts using AI.

Users can upload a contract (PDF or image), and the system extracts key details, identifies potential risks, evaluates the deal, and allows users to ask questions about it.

---

## ⚙️ How It Works

1. User uploads a contract file
2. Text is extracted using OCR (PyMuPDF + Tesseract)
3. Gemini AI analyzes the contract
4. System extracts key details and risks
5. A fairness score and summary are generated
6. User can interact with the contract using a chatbot

---

## ✨ Features

* 📄 Upload contract (PDF / image)
* 🔍 OCR-based text extraction
* 🧠 AI extraction of:

  * Monthly Payment
  * Lease Term
  * APR (if present)
  * Risk clauses
* 📊 Fairness score (0–100)
* ⚠️ Risk detection
* 💡 Suggestions based on contract
* 🤖 Chatbot to ask questions about the contract
* 🎨 Simple dashboard UI with chat

---

## 🛠️ Tech Stack

* **Backend:** FastAPI (Python)
* **AI Model:** Google Gemini
* **OCR:** PyMuPDF + Tesseract
* **Frontend:** HTML, CSS, JavaScript

---

## 📁 Project Structure

```
car_contract_ai/
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── home.html
│   └── index.html
└── README.md
```

## 🚀 How to Run

### Backend

cd backend
pip install -r requirements.txt

Set API key:
set GOOGLE_API_KEY=your_api_key

Run server:
uvicorn main:app --reload

---

### Frontend

cd frontend
python -m http.server 5500

Open in browser:
http://localhost:5500/home.html

---

## 📊 Example Output

```json
{
  "analysis": {
    "monthly_payment": "₹62,500",
    "lease_term": "48 months",
    "risks": ["Excess mileage fee"]
  },
  "evaluation": {
    "risk_level": "Medium",
    "fairness_score": 65
  },
  "suggestions": [
    "Try negotiating the monthly payment",
    "Ask for a higher mileage limit"
  ]
}
```

## ⚠️ Disclaimer

This tool provides AI-generated insights and may not always be fully accurate.
It should not be used as a substitute for professional legal or financial advice.

---

## 👩‍💻 Author

Anushka Bhatt
