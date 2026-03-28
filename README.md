# 🚗 Car Lease Analyzer

> **AI-powered lease contract analysis & negotiation platform**  
> Upload any car lease document, extract every clause with Claude AI, look up vehicle history, and get personalised negotiation advice — all in one dark-themed Streamlit app.

---

## 📸 Screenshots

| Screen | Description |
|---|---|
| Sign In | Dark navy + orange login page with animated floating car |
| Sign Up | Public registration — no invite required |
| Extract SLA | PDF upload → AI extraction → Table / JSON view + 4 charts |
| VIN Report | 17-char counter, NHTSA lookup, recall history |
| Negotiate | AI chatbot with quick-prompt chips and chat bubbles |

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
- "Load Demo Data" shortcut when no file is selected

**Extraction**
- `🔍 Extract SLA Details` button triggers Claude `claude-sonnet-4-6`
- Animated progress bar with "Extracting SLA Data…" and "Processing PDF…" status
- Falls back to rich BMW demo data when no API key is set

**Results — Table View (8 sections)**

| Section | Fields |
|---|---|
| Document Information | Type, Date, Contract Number |
| Parties | Lessor name/address, Lessee name/address |
| Vehicle Information | VIN, Brand, Model, Variant, Body Type, Fuel Type |
| Financial & Lease Terms | Start/End dates, Duration, Monthly payment, Down payment, Security deposit, Total cost |
| Mileage Terms | Annual limit, Total limit, Excess charge per km |
| SLA Obligations | Maintenance, Insurance, Wear & tear, Early termination fee, Late payment fee |
| End of Lease Options | Purchase option, Residual value, Return conditions |
| Additional Terms | Bullet-list of all remaining clauses |

**Results — JSON View**
- Toggle between Table and `{ } JSON` view
- `📥 Export JSON` download button


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
| `demo@demo.com` | `demo123` | Secondary demo account |

Or click **Sign up** to create your own account — registration is open to all users.
---


## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.32.0 | UI framework — all pages, tabs, widgets |
| `anthropic` | ≥ 0.25.0 | Claude AI SDK — SLA extraction + chat |
| `python-dotenv` | ≥ 1.0.0 | Load `.env` variables |
| `plotly` | ≥ 5.20.0 | Radar, bar, donut, comparison charts |
| `requests` | ≥ 2.31.0 | NHTSA VIN decode + recall API calls |
| `Pillow` | ≥ 10.0.0 | Image preview for uploaded lease photos |

---

## 🎨 Design System

| Element | Value |
|---|---|
| Background | `#0F172A` → `#1E1533` gradient (dark navy) |
| Primary accent | `#F97316` (orange) |
| Accent dark | `#EA580C` |
| Text primary | `#F1F5F9` |
| Text muted | `#94A3B8` |
| Success | `#22C55E` |
| Warning | `#F59E0B` |
| Danger | `#EF4444` |
| Font UI | Inter (300–900) |
| Font mono | JetBrains Mono |
| Border radius | 10px (inputs), 12–14px (cards) |

---

## 🤖 AI Model

| Feature | Model |
|---|---|
| SLA document extraction | `claude-sonnet-4-6` |
| Lease negotiation chat | `claude-sonnet-4-6` |

The SLA extractor sends the full document (PDF as base64, image as base64) along with a structured JSON prompt that specifies every field to extract — including vehicle details, financial terms, mileage, obligations, red flags, fairness score, and market comparison.

The negotiation advisor builds a system prompt that embeds the complete extracted lease JSON as context, so every chat response is aware of your specific contract terms.

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
