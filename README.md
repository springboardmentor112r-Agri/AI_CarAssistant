#  AI Car Lease / Loan Contract Assistant

## 1. Overview

This project is an AI-based system designed to analyze car lease or loan contracts. It extracts key financial terms, evaluates risk, and provides decision support to help users understand contract details and avoid unfavorable agreements.


## 2. Objectives

* Simplify complex lease/loan contracts
* Identify key financial parameters
* Detect risks and hidden clauses
* Assist users in decision-making


## 3. Features

### 3.1 Contract Analysis

Extracts important details from uploaded PDF:

* APR (interest rate)
* Monthly payment
* Loan duration
* VIN number
* Penalties and red flags


### 3.2 Risk Evaluation

* Contract Quality Score (0–100)
* Risk Percentage
* Risk Classification (Low / Moderate / High)


### 3.3 Price Estimation

* Estimates vehicle price using VIN/year logic
* Provides approximate price range
* Helps assess deal fairness


### 3.4 Decision Support

* Final Verdict (Good / Caution / Not Recommended)
* Explanation of results
* Suggested improvements


### 3.5 Contract Comparison

* Compare two contracts
* Identify better option based on APR


### 3.6 Chat Assistant

* Answers user queries related to:

  * APR
  * Risk
  * Contract quality
  * Price estimation


## 4. System Architecture

```
User Input (PDF)
      ↓
Text Extraction (PyPDF2)
      ↓
Data Extraction (Regex)
      ↓
Risk Calculation
      ↓
Price Estimation
      ↓
Decision & Insights
      ↓
Frontend Display
```



## 5. API Endpoints

| Endpoint  | Method | Description           |
| --------- | ------ | --------------------- |
| /analyze/ | POST   | Analyze contract      |
| /compare/ | POST   | Compare two contracts |
| /chat/    | GET    | Chat assistant        |



## 6. Technology Stack

* Backend: FastAPI (Python)
* Text Processing: PyPDF2
* Data Extraction: Regex
* Frontend: HTML, CSS, JavaScript

## 7. Installation & Execution

### Backend

```bash
uvicorn main:app --reload
```

### Frontend

Open `index.html` in browser


## 8. Key Functionalities

* Automated contract parsing
* Risk scoring mechanism
* Price estimation logic
* Interactive chatbot
* Visual risk indicator


## 9. Limitations

* Uses rule-based extraction (not full AI model)
* Price estimation is approximate
* Limited VIN decoding


## 10. Future Enhancements

* Integration with LLMs (GPT)
* Real-time vehicle pricing APIs
* Advanced NLP for contract understanding
* Deployment as full-scale web/mobile app



## 11. Conclusion

This system improves transparency in car lease/loan agreements by providing automated analysis, risk evaluation, and decision support, enabling users to make informed financial choices.


Bhavya S

