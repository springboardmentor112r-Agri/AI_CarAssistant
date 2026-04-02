# 🚗 Car Lease Analyzer

> **AI-powered lease contract analysis & negotiation platform**  
> Upload any car lease document, extract every clause with Claude AI, look up vehicle history, and get personalised negotiation advice — all in one dark-themed Streamlit app.

---

## ✨ Features

### 🔐 Authentication (Public — Open to All)
- **Sign In** with email + password — "Please wait…" loading state on submit
- **Sign Up** — anyone can register (name, email, password, confirm)
- Passwords hashed with SHA-256; user store in session state (swap to a DB for production)
- Auto sign-in immediately after successful registration
  
---

### 📄 Tab 1 — Extract SLA
Upload a car lease document and let Claude AI extract every detail automatically.

**Upload**
- Accepts JPG, PNG, PDF up to 20 MB
- Drag-and-drop or click-to-browse zone
- Document Preview card — image preview for photos, file name + size for PDFs

**Extraction**
- `🔍 Extract SLA Details` button triggers Claude `claude-sonnet-4-6`
- Animated progress bar with "Extracting SLA Data…" and "Processing PDF…" status

**Results — Table View (8 sections)**

| Section | Fields |
|---|---|
| Document Information | Type, Date, Contract Number |
| Parties | Lessor name/address, Lessee name/address |
| Vehicle Information | VIN, Brand, Model, Variant, Body Type, Fuel Type |
| Financial & Lease Terms | Start/End dates, Duration, Monthly payment, Down payment, Security deposit, Total cost |

**Results — JSON View**
- Toggle between Table and `{ } JSON` view
- `📥 Export JSON` download button

---

### 🔍 Tab 2 — VIN Report
Look up any vehicle by its VIN number using the free NHTSA public API.

- Large text input with placeholder `ENTER 17-CHARACTER VIN (E.G. 1HGCM82633A123456)`
- Character counter `0/17` — **turns orange** when all 17 characters are entered
- `Get Report` button triggers live NHTSA API call
- Pre-fills VIN automatically from any extracted lease document

**Results**
- Vehicle title card with VIN in monospace
- **Basic Information** — Make, Model, Year, Series/Trim, Body Class, Drive Type
- **Technical Specifications** — Fuel Type, Engine (L), Cylinders, Seats, Doors, Manufacturer, Plant Country
- **Recall History** — green badge (0 recalls) or red badge (N recalls) with component + description per recall
- **Full History Report** — links to Carfax (paid) and AutoCheck for accident/odometer history
- Falls back to BMW demo data when offline

---

### 💬 Tab 3 — Negotiate
AI-powered negotiation advisor that uses your loaded lease contract as live context.

**Empty State**
- Orange chat icon, "Lease Negotiation Advisor" heading
- "Your loaded lease data is available as context." shown when a lease is loaded
- **5 quick-action prompt chips** (exact text from the app):
  - What lease terms are typically negotiable?
  - Explain my monthly payment and what affects it
  - How can I reduce excess mileage penalties?
  - What should I watch out for before signing?
  - Help me understand my end-of-lease options

**Chat Interface**
- User messages: right-aligned orange gradient bubble
- AI responses: left-aligned dark card bubble with formatted markdown
- Input bar: `Ask about lease terms, negotiation tactics…` placeholder + orange ➤ send button
- `🗑 Clear conversation` link to reset chat history
- Claude receives the full extracted lease JSON as system-level context
- Falls back to contextual demo responses without an API key

---

## 📁 Project Structure

```
car_lease_v2/
│
├── streamlit_app.py          # ⚡ Entry point — theme, auth gate, 3-tab layout
├── .env                      # Your API keys
├── requirements.txt          # Python dependencies
├── README.md
│
├── auth/
│   ├── __init__.py
│   └── user_auth.py          # Sign In, Sign Up, session management
│
├── sla/
│   ├── __init__.py
│   └── extractor.py          # Tab 1 — PDF upload, Claude AI extraction
│
├── vin/
│   ├── __init__.py
│   └── report.py             # Tab 2 — VIN decode + recall lookup via NHTSA
|
├── negotiate/
│   ├── __init__.py
│   └── advisor.py            # Tab 3 — AI chatbot with lease context
│
└── utils/
    └── __init__.py           # Shared utilities (extend as needed)
```

---

## 🚀 Quick Start

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
streamlit run streamlit_app.py
```

The app opens at **http://localhost:8501**

---

## 🔑 Demo Accounts

| Email | Password | Notes |
|---|---|---|
| `Akhil@test.com` | `password123` | Primary demo account |
| `demo@demo.com` | `demo123` | Secondary demo account |

Or click **Sign up** to create your own account — registration is open to all users.
---

## 🌐 NHTSA API (Free — No Key Needed)

The VIN Report tab uses two free public endpoints from the US National Highway Traffic Safety Administration:

```
https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{VIN}?format=json
https://api.nhtsa.gov/recalls/recallsByVehicle?make={}&model={}&modelYear={}
```

No API key, no rate limit registration required. Falls back to demo data if the API is unreachable.

---

## 📋 How Each Tab Connects

```
User uploads PDF
        │
        ▼
  📄 Extract SLA
        │
        ├──── VIN auto-extracted from lease
        │              │
        │              ▼
        │       🔍 VIN Report
        │       (pre-filled VIN, live NHTSA lookup)
        │
        └──── Lease data injected as AI context
                       │
                       ▼
                💬 Negotiate
                (AI knows your monthly payment, mileage limits, red flags, etc.)
```

*🚗 Car Lease Analyzer &nbsp;•&nbsp; AI-Powered Lease Intelligence &nbsp;•&nbsp; Developed by S-A-M*
