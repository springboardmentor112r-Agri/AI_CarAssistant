AI Car Lease/Loan Contract Review Assistant
 Overview
This project is an AI-based system designed to analyze car lease or loan contracts. It extracts important financial and legal information from contract documents and provides structured insights, risk evaluation, and decision support to help users make informed choices.

Features

Contract Analysis
- Upload contract PDF
- Extract key details:
  - Interest Rate (APR)
  - Monthly Payment
  - Lease Duration
  - VIN Number
  - Penalty clauses

 Risk & Decision Analysis
- Contract Quality Score
- Risk Percentage and Risk Level (Low / Moderate / High)
- Financial Risk and Legal Risk categorization
- Final Verdict (Good Deal / Caution / Not Recommended)

 Intelligent Insights
- Red Flag detection (penalty, termination, etc.)
- Explainable output ("Why this result")
- Key Issue identification
- Decision Guide for users

 Negotiation Support
- Smart suggestions for improving contract terms

Contract Comparison
- Compare two contracts
- Identify better contract based on APR
- Provide reasoning

Conversational Assistant
- Simple chatbot to answer queries about contract terms



Complete Workflow

1. User uploads a contract PDF
2. System extracts text using PyPDF2
3. Important values are identified using pattern matching:
   - APR
   - Payment
   - Duration
   - VIN
   - Penalties
4. Data is structured into a readable format
5. Risk analysis is performed using rule-based logic
6. Red flags and key issues are identified
7. Suggestions and decision guidance are generated
8. Output is displayed via FastAPI Swagger UI


Tech Stack

- Python
- FastAPI
- PyPDF2
- Regex (pattern-based extraction)
- Swagger UI (API interface)



 Sample Output

- APR: 9.25%
- Monthly Payment: ₹18,500
- Risk Level: Moderate
- Contract Quality Score: 80
- Final Verdict: Proceed with Caution

 Demo Video


System Design Approach

- Focus on backend intelligence and contract understanding
- Rule-based analysis for risk evaluation
- Explainable outputs for better user understanding
- Designed as a scalable system that can integrate AI models

 Future Scope

- Integration with Large Language Models (LLMs)
- VIN-based vehicle data APIs
- Real-time vehicle price estimation
- Full frontend (web/mobile application)
- Advanced negotiation chatbot



Swagger UI is used as the frontend interface for interaction and demonstration.

