# 🚗 LeaseGuard AI

**Car Lease/Loan Contract Review & Negotiation AI Assistant**
**Presented by:** Soumik Samanta

---

## 📌 Overview

**LeaseGuard AI** is an intelligent web-based assistant designed to help users understand, review, and negotiate car lease or loan contracts. The platform leverages OCR, AI, and vehicle data decoding to extract, analyze, and evaluate contract terms for fairness and transparency.

This project aims to reduce confusion in complex automotive financial agreements by providing automated insights, fairness scoring, and AI-powered negotiation suggestions.

---

## 🎯 Key Features

* 📄 **Contract Text Extraction** using OCR
* 🚘 **Vehicle Identification & Details** using VIN decoding
* 🤖 **AI Contract Analysis** powered by LLM
* 📊 **Fairness Score Generation** to evaluate contract quality
* 💬 **AI Negotiation Assistant** to help users respond to dealership terms
* 🌐 **User-Friendly Web Interface** built with HTML, CSS, and JavaScript

---

## 🧠 How It Works

1. **Upload Contract PDF**

   * The user uploads a car lease or loan agreement.

2. **Text Extraction**

   * The system extracts text using:

     * `pdfplumber`
     * `pdf2image`
     * `Tesseract OCR`

3. **Vehicle Data Processing**

   * VIN is extracted and decoded using the **NHTSA VIN dataset** to retrieve vehicle details.

4. **AI Analysis**

   * Extracted contract text is analyzed using a Large Language Model via **Groq API**.
   * The AI identifies key clauses, risks, and unusual terms.

5. **Fairness Scoring**

   * The system evaluates contract conditions and generates a fairness score to help users quickly understand whether the agreement is balanced.

6. **Negotiation Assistant**

   * Users can interact with an AI chatbot to receive suggestions on how to negotiate better lease/loan terms.

---

## 🛠️ Tech Stack

### Backend & AI

* **Python**
* **pdfplumber** – PDF text extraction
* **pdf2image** – Convert PDF pages to images
* **Tesseract OCR** – Optical character recognition
* **Groq API** – LLM inference engine
* **NHTSA VIN Dataset** – Vehicle decoding and metadata

### Frontend

* **HTML**
* **CSS**
* **JavaScript**

---

## 🖥️ User Interface Features

The website provides the following user-facing modules:

* Vehicle Details Panel (decoded from VIN) with Fairness Score Dashboard
* Contract Summary Section in Json Format
* AI Chat Interface for negotiation guidance

---

## 📂 Project Structure (Suggested)

```
LeaseGuardAI/
│
├── backend/
│   ├── auth.py
│   ├── chatbot.py
│   ├── database.py
│   ├── fairness.py
│   ├── Ilm_engine.py
│   ├── main.py
│   ├── pdf_jpg_ocr.py
│   ├── redflags.py
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── styles.css
│   └── script.js
│
├── assets/
│   └── sample_contracts/
│
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

* Python 3.9+
* Tesseract OCR
* Poppler (for pdf2image)

### Installation

```bash
git clone https://github.com/your-username/LeaseGuardAI.git
cd LeaseGuardAI
pip install -r requirements.txt
```

### Run the Project

```bash
python main.py
```

Then open your browser and visit:

```
http://localhost:5000
```

---

## 🔍 Example Use Cases

* Reviewing dealership lease agreements before signing
* Comparing fairness across multiple loan contracts
* Understanding hidden clauses and penalties
* Getting AI-generated negotiation strategies

---

## 🚀 Future Improvements

* 📊 Real-time dealership contract comparison
* 🌐 Support for multiple languages
* 📱 Mobile responsive UI enhancements
* 💳 Integration with financial APIs for rate benchmarking

---

## 🤝 Contribution

Contributions, issues, and feature requests are welcome. Feel free to fork the repository and submit a pull request.

---

## 📜 License

This project is intended for educational and research purposes.

---

## 👨‍💻 Author

**Soumik Samanta**

Infosys Springboard Internship

Engineering Student | AI  Enthusiast 
