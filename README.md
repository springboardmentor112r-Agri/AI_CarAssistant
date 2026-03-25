# AI Car Lease Analysis Agent




https://github.com/user-attachments/assets/7b459cef-9efa-4252-a327-09acfea1906c




## Project Overview

The **Car Lease or Loan Contract Review and Negotiation App** is an AI-driven application designed to help users understand, review, and negotiate car lease or loan contracts with greater confidence. It uses Large Language Models (LLMs) for SLA/contract clause extraction, identifies key terms in lease documents, and improves transparency by cross-verifying vehicle pricing and history using publicly available data sources.

## Goal of the Project

The primary goal of this project is to:

* Enable users to review and interpret car lease/loan contracts easily.
* Provide AI-based extraction of critical clauses such as interest rates, mileage limits, penalties, and early termination conditions.
* Offer fair market value benchmarks and car history reports to support negotiation decisions.

Users can upload a lease document and instantly receive:

* 📝 Simple summaries
* ⚠️ Risk analysis
* 🚘 VIN verification and Report
* 🤖 AI-powered answers


## Key Features

### 1) Document Upload

* Supports **PDF** and **image** uploads.
* Automatically extracts lease or loan data from uploaded files.

### 2) OCR Extraction

* Converts scanned or image-based documents into readable text.
* Helps process documents that are not digitally selectable.

### 3) AI Lease Analysis

* Extracts important lease fields such as:

  * Monthly payment
  * Interest rate
  * Mileage limits
  * Fees
* Helps users understand contract terms faster.

### 4) Fairness Score

* Generates a **0–100 fairness score**.
* Gives a quick view of how favorable or risky the deal looks.

### 5) Red Flags Detection

* Highlights risky contract conditions as:

  * High
  * Moderate
  * Low
* Helps users spot hidden charges and unfavorable clauses.

### 6) VIN Verification (NHTSA API)

* Extracts or accepts a VIN from the user.
* Verifies:

  * Manufacturer
  * Model
  * Year
  * Vehicle type

### 7) AI Chatbot

* Allows users to ask questions about the uploaded lease or loan document.
* Provides simple answers based on extracted contract data.

## System Architecture

```text
User Uploads Document (PDF / Image)
↓
OCR Module (OCR / pdfplumber)
↓
Data Extraction Module
↓
Decision Logic (Risk Identification)
↓
VIN Verification (NHTSA API)
↓
Structured Output + Chatbot
```

## Modules Implemented

* ✅ OCR Module — OCR + pdfplumber for document extraction
* ✅ AI Analysis — OpenRouter API for lease understanding
* ✅ Fairness Scoring — Rule-based lease risk detection
* ✅ VIN Verification — NHTSA API integration
* ✅ AI Chatbot — Answers user queries
* ✅ Frontend Dashboard — Streamlit
* ✅ Backend API — FastAPI

## Project Structure

```text
OCR/
├── .vscode/
│   └── settings.json
├── agents_ai/
│   ├── __pycache__/
│   ├── agents/
│   │   ├── __pycache__/
│   │   ├── coordinator_agent.py
│   │   ├── document_handler_agent.py
│   │   ├── preprocessing_agent.py
│   │   ├── risk_analysis_agent.py
│   │   ├── sla_extraction_agent.py
│   │   ├── summary_agent.py
│   │   ├── validation_agent.py
│   │   └── Vin.py
│   ├── storage/
│   └── uploads/
├── .env
├── backend_app.py
├── frontend_app.py
├── main.py
└── requirements.txt
```

## How to Test

1. Upload a lease document in **PDF** or **image** format.
2. View the extracted data and risk score.
3. Test VIN verification using a valid VIN.
4. AI Assitant

## Future Improvements

* User authentication
* Document comparison analysis
* Advanced negotiation suggestions
* Exportable reports in PDF/CSV format

