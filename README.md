# 🚗 AI Car Lease Contract Analyzer & Negotiation Assistant

**👩‍💻 Done By:** Nikitha Nair  
**🎯 Project:** Car Lease/Loan Contract Review and Negotiation AI Assistant 

---

<h2 align="center">🎥 Watch Project Demo</h2>

<p align="center">
  <a href="https://youtu.be/bIUThngRR6c">
    <img src="https://img.youtube.com/vi/bIUThngRR6c/0.jpg" width="700">
  </a>
</p>


## 📌 Project Overview

An AI-powered web application that simplifies car lease agreements by extracting key details, evaluating fairness, identifying risks, and providing intelligent negotiation assistance through an interactive chatbot.

---

## 🧠 System Workflow

| Step | Process |
|------|--------|
| 1 | 📄 Upload Contract (PDF / Image) |
| 2 | 🔍 Text Extraction (OCR / PDF Parser) |
| 3 | 🧾 Structured Data (JSON) |
| 4 | ⚖️ Fairness Score & Risk Detection |
| 5 | 🚗 VIN Lookup (Vehicle Verification) |
| 6 | 🤖 AI Chatbot Interaction |
| 7 | 📊 User-Friendly Output (Table + Insights) |


---

## ✨ Key Features

- 📄 **Smart Contract Upload**
  - Supports PDF and image-based lease agreements

- 🔍 **Automatic Data Extraction**
  - Extracts key fields like payment, mileage, duration

- 📊 **Fairness Score Calculation**
  - Score (0–100) based on financial factors

- ⚠️ **Risk Detection**
  - Identifies red flags (high payment, low mileage, etc.)

- 🤖 **AI Negotiation Assistant**
  - Answers user queries
  - Provides negotiation suggestions
  - Uses fairness score + risk level

- 🚗 **VIN Lookup**
  - Fetches vehicle details using API

- 🎨 **Interactive UI**
  - Dark theme with modern design
  - JSON and Table view
  - Chat-style interface

---

## 🛠️ Tech Stack

### 🔹 Backend
- Flask
- Flask-SQLAlchemy
- Flask-Login

### 🔹 AI & APIs
- Groq API (LLM for chatbot)
- REST APIs (VIN lookup)

### 🔹 Data Processing
- pdfplumber (PDF extraction)
- pytesseract (OCR)
- Pillow (Image processing)

### 🔹 Frontend
- HTML
- CSS (Dark Theme UI)
- JavaScript

### 🔹 Database
- SQLite

---

## 📁 Project Structure

```
AI_Lease_Assistant/
│── app.py
│── requirements.txt

├── templates/
│   ├── dashboard.html
│   ├── upload.html
│   ├── result.html
│   ├── fairness.html
│   └── chat.html

├── static/
│   └── style.css

├── utils/
│   ├── pdf_reader.py
│   ├── ocr_reader.py
│   ├── ai_analyzer.py
│   └── fairness.py

└── uploads/
```


---

## 🚀 How to Run

### 1️⃣ Clone Repository

git clone -b AI_CarAssistant-NikithaNair https://github.com/springboardmentor112r-Agri/AI_CarAssistant.git

cd AI_CarAssistant


---

### 2️⃣ Install Dependencies

pip install -r requirements.txt


---

### 3️⃣ Setup Environment Variables

Create a `.env` file:

GROQ_API_KEY=your_api_key_here


---

### 4️⃣ Run Application

python app.py


---

### 5️⃣ Open in Browser

http://127.0.0.1:5000


---

## 📊 Core Modules

| Module            | Purpose                                  |
|------------------|------------------------------------------|
| Text Extraction  | Extract data from PDF/Image              |
| AI Analysis      | Understand contract using LLM            |
| Fairness Engine  | Calculate score and detect risk          |
| VIN Lookup       | Validate vehicle details                 |
| Chatbot          | Answer queries + negotiation help        |
| UI Layer         | User interaction                         |

---

## 🧪 Test Scenarios

| Feature  | Input                | Expected Output                    |
|---------|---------------------|----------------------------------|
| Upload  | Lease PDF           | Structured contract data         |
| OCR     | Image contract      | Text extracted correctly         |
| Fairness| High cost contract  | Low score + red flags            |
| Chatbot | "Is this a good deal?" | Risk-aware response          |
| VIN     | Valid VIN           | Vehicle details displayed        |

---

## 🧠 Fairness Logic

- Score starts from **100**
- Deducted based on:
  - Monthly payment
  - Down payment
  - Mileage limit
  - Lease duration
- Additional penalty applied per red flag

---

## 💬 Chatbot Capabilities

- Context-aware responses  
- Uses:
  - Contract data  
  - Fairness score  
  - Risk level  

- Provides:
  - Direct answers  
  - Explanations  
  - Negotiation suggestions  

---

## 🔮 Future Enhancements

- 📊 Deal comparison  
- 📂 Contract history dashboard  
- 📱 Mobile-friendly UI  
- 🧠 Advanced AI scoring  
- 🌐 Cloud deployment  

---

## 👩‍💻 Author

**Nikitha Nair**  
Infosys Springboard Internship

---

## ⭐ Final Note

This project demonstrates how AI can simplify complex lease agreements and help users make smarter financial decisions.

---


