# Car Lease/Loan Contract AI Assistant

An advanced AI-powered assistant to review car lease/loan contracts using **Computer Vision**, **OCR**, and automated processing.

![Milestone 2 Complete](https://img.shields.io/badge/Milestone-2_Complete-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)

## 🚀 Key Features

### 🤖 AI Negotiation Chatbot (Milestone 3)
- **Interactive Web Interface**: Premium dark-mode chat interface for real-time negotiation help.
- **Context-Aware AI**: Powered by **Google Gemini 2.5 Flash** (via `google-generativeai`),groq.
  - Reads processed VIN data + Market Value.
  - Suggests counter-offers and detects dealer tricks (fees/addons).
- **Dual-Mode Logic**:
  - **AI Mode**: Full natural language advice (requires API Key).
  - **Fallback Mode**: Rule-based logic if no API key is present.

### 💹 Market Value Analysis (Milestone 4)
- **Enhanced VIN Decoding**: Integrated with **NHTSA API** to extract Year, Make, Model, Trim, Engine Specs, and Safety Features.
- **Fair Price Estimation**: Built-in valuation engine that calculates estimated market value.
  - Uses linear depreciation model as a smart fallback.
  - Supports plug-in architecture for external pricing APIs (like KBB/MarketCheck).
- **Result Caching**: Implemented caching to speed up repeated queries and reduce API load.

### 👁️ Advanced OCR & Computer Vision
- **Hybrid Extraction**: Uses `pdfplumber` for digital PDFs and `Tesseract` + `OpenCV` for scanned documents.
- **Image Preprocessing**:
  - **Adaptive Thresholding**: Handles shadows and uneven lighting.
  - **Noise Reduction**: Removes coffee stains and scan artifacts.
  - **Deskewing**: Straightens crooked scans.
- **Persistent Storage**: Automatically saves all extracted data to a local SQLite database.

---

## 📁 Project Structure

```
car-lease-loan-ai-assistant/
├── backend/
│   └── app/
│       ├── ocr.py            # Hybrid OCR Engine (Tesseract + pdfplumber)
│       ├── preprocessing.py  # OpenCV Image Cleanup Module (M2)
│       └── database.py       # SQLite Database Operations
├── docs/                     # Documentation
│   └── Milestone2_Processing.md
├── visual_test.py            # Debug tool: Before/After preprocessing images
├── accuracy_test.py          # Tool: Measure OCR improvement
├── check_db.py               # Tool: View database records
├── requirements.txt          # Project dependencies
└── README.md
```

## 🛠️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Intern-22222/car-lease-loan-ai-assistant.git
   cd car-lease-loan-ai-assistant
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Includes `opencv-python`, `sqlalchemy`, `pytesseract`.*

3. **Install Tesseract OCR**
   - **Windows**: [Download Backend](https://github.com/UB-Mannheim/tesseract/wiki) and install to default path.
   - **Linux**: `sudo apt install tesseract-ocr`
   - **Mac**: `brew install tesseract`

## 🧪 Verification Tools

We built specific tools to verify the improvements in Milestone 2:

| Tool | Command | Description |
|---------------|-------------|
| **Visual Debugger** | `python visual_test.py` | Generates "Before vs After" images in `visual_output/` folder. |
| **Accuracy Test** | `python accuracy_test.py` | Compares character counts between raw and cleaned OCR. |
| **Database Viewer** | `python check_db.py` | lists all saved contracts in the local database. |

## 📋 Deliverables Progress
### ✅ Milestone 4: External Data & Valuation (Current)
- [x] VIN Decoder Module (`vin_decoder.py`) - NHTSA Integration
- [x] Valuation Engine (`valuation.py`) - Depreciation logic
- [x] Unified API Endpoint (`api.py`)
- [x] Caching & Performance Optimization

### ✅ Milestone 2: Advanced Processing & Sotrage
- [x] OpenCV Preprocessing Module (`preprocessing.py`)
- [x] SQLite Database Integration (`database.py`)
- [x] Verification Scripts (`visual_test.py`, `accuracy_test.py`)
- [x] Technical Documentation

### ✅ Milestone 1: Foundation
- [x] Basic Tesseract & pdfplumber setup
- [x] Unit Tests
- [x] Local Environment Setup

## 📜 License
MIT License
