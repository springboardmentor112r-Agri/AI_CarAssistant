# DealGuard: AI-Driven Contract Auditor

**DealGuard** is a minimalist, high-precision digital auditor designed to dismantle the **"Jargon Barrier"** in automotive financing. By combining high-speed PDF extraction with a weighted risk-scoring algorithm, it transforms 50-page predatory contracts into clear, actionable safety reports.

##  Installation and Setup.
First launch the backend using the link below.
| Component | Access Link |
| :--- | :--- |
| **Live Backend** | [Launch DealGuard backend](https://ai-carassistant-1.onrender.com/) |
| **Current Branch** | `AI_CarAssistant-Pavithra` |

**Note** : The backend is hosted on Render (free tier). The first request may take 30-60 seconds due to inactivity.

Next, launch the frontend as follows :
### 1\. Clone the Repository

```bash
git clone https://github.com/PavithraSageer/AI_CarAssistant.git
cd AI_CarAssistant
git checkout AI_CarAssistant-Pavithra
-----
```
### 2\. Setup Frontend (The Interface)
```bash
cd frontend
npm install
npm run dev
```

##  The Core Mission

Car buyers often face **"Legal Fatigue,"** signing dense contracts containing hidden fees and "As-Is" clauses. DealGuard acts as a **Digital Shield**, using AI to extract the 5% of text that actually impacts the buyer's wallet.

##  The Tech Stack

  * **Frontend:** React.js (Clean, Sidebar-free UI for cognitive focus)
  * **Backend:** FastAPI (High-concurrency Python framework)
  * **Database:** Supabase (PostgreSQL with Row-Level Security)
  * **AI Engine:** Arcee Trinity-Mini (Tuned to 0.3 Temperature for factual precision)
  * **Parsing:** PyMuPDF (fitz) & Regex Pattern Matching

-----

##  Key Features

### 1\. The X-Ray Pipeline

Uses **PyMuPDF** to bypass slow OCR, extracting the raw text layer in milliseconds. Custom Regex logic identifies the 17-character VIN and financial figures before the AI starts, ensuring 100% accuracy on vehicle data.

### 2\. Weighted Fairness Algorithm

Instead of subjective summaries, DealGuard calculates a **Fairness Score (0–100)** based on specific legal triggers:

  * **-35 Points:** "As-Is" / No Warranty clauses.
  * **-20 Points:** Uncapped Administrative Fees.
  * **-15 Points:** Ambiguous Arbitration Waivers.

### 3\. Jargon-to-English Chatbot

A specialized implementation of the **Trinity-Mini LLM**. Tuned for low-temperature (0.3) determinism, it translates complex legalese into 5th-grade English without "hallucinating" advice.

-----

##  Future Roadmap

  * **Automated Negotiation:** Generating structured dispute letters based on detected red flags.
  * **Domain Expansion:** Porting logic to Home Rental Agreements and Insurance Policies.
  * **Historical Benchmarking:** Tracking dealership patterns to identify recurring predatory behavior.

-----

##  Screenshots and Demo
[**Click here to view screenshots, demo video and PPT**](https://drive.google.com/drive/folders/1o1YZho_Hr_IOBrh6dQpSdfudUfcYgj3v)

-----

##  Author

**Pavithra S** *AI Domain Intern | Computer Science & Engineering*



