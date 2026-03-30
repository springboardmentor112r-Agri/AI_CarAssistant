# AI Car Lease / Loan Contract Assistant

##  About the Project
Understanding car lease and loan contracts is difficult. These documents are long, filled with legal jargon, and often hide important financial details.

This project solves that problem by acting as an **AI-powered assistant** that simplifies contracts and helps users make better decisions.



##  Problem Statement
Many users:
- Don’t fully understand **interest rates (APR)**
- Overlook **penalties and hidden charges**
- Cannot judge if a deal is **good or risky**

 Result: Poor financial decisions and unexpected costs



## Solution
An intelligent system that:
- Extracts key data from contracts
- Analyzes financial risk
- Explains everything in simple language
- Helps users decide confidently



## Core Features

### Contract Analysis
- Upload PDF contract
- Extract:
  - APR (interest rate)
  - Monthly payment
  - Duration
  - VIN number



###  Risk Analysis
- Contract score (0–100)
- Risk percentage
- Risk level:
  - Low
  - Moderate
  - High



###  Decision Support
- Final verdict:
  -  Good Deal  
  -  Proceed with Caution  
  -  Not Recommended  
- Reasons + Suggestions
- Clear decision guide



###  Contract Comparison
- Upload 2 contracts
- System compares:
  - Risk score
  - Financial terms
- Suggests better option


###  Chat Assistant
Ask questions like:
- What is APR?
- What is risk?
- Is this a good deal?

 Instant simple explanations



## System Workflow
User Upload
↓
PDF Text Extraction (PyPDF2)
↓
Data Extraction (Regex)
↓
Risk Analysis Engine
↓
Insights + Decision Output



## Tech Stack

- **Backend:** Python, FastAPI  
- **PDF Processing:** PyPDF2  
- **Logic:** Regex + Rule-based system  
- **Frontend:** HTML, CSS, JavaScript  



## How to Run

###  Start Backend
 uvicorn main:app --reload

 ### Open Frontend
  Open index.html in browser

## Why This Project Matters
Simplifies complex contracts
Saves time
Increases financial awareness
Highlights hidden risks
Helps users avoid bad deals


## Future Improvements
 AI-based contract understanding (LLMs)
 VIN API integration (vehicle details)
 Smart visual dashboards
 User login system
 Full web/mobile deployment
 
## My Contribution
Designed complete idea & system flow
Built FastAPI backend
Developed risk analysis engine
Created UI + frontend logic
Implemented chatbot

## API Endpoints
/analyze/ → Analyze contract
/compare/ → Compare two contracts
/chat/ → Chat assistant
