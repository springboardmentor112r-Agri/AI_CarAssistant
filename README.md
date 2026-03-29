# AI Car Lease / Loan Contract Assistant

## About this project

I realized how difficult it is to understand. These documents are long, full of legal terms, and most people don’t really know what they are signing.


The goal is simple:  
Take a complex contract and explain it in a way anyone can understand.



## What problem I am solving

Many people:
- Don’t understand interest rates properly  
- Miss penalty clauses  
- Don’t know if a deal is good or bad  

Because of this, they can end up making poor financial decisions.



## My idea

The idea behind this project is to act like a personal assistant for car contracts.

Instead of reading everything manually, the user can:
1. Upload the contract  
2. Let the system analyze it  
3. Get a clear explanation and decision  



## What the system does

### Contract Analysis
The user uploads a PDF contract.  
The system extracts:
- Interest rate (APR)
- Monthly payment
- Duration
- VIN number
- Penalties



### Risk Analysis
The system evaluates how risky the contract is:
- Contract Quality Score (out of 100)
- Risk percentage
- Risk level (Low, Moderate, High)



### Decision Support
The system helps the user decide:
- Final verdict (Good Deal / Proceed with Caution / Not Recommended)
- Explanation of result
- Suggestions for improvement
- Decision guide



### Contract Comparison
- Upload two contracts  
- System compares them  
- Suggests the better contract  



### Chat Assistant
User can ask questions like:
- What is APR?
- What is risk?
- Is this contract good?

The chatbot gives simple answers and can also use the analyzed contract.



## How it works (simple flow)

1. User uploads contract  
2. System reads PDF using PyPDF2  
3. Important data is extracted using regex  
4. Risk is calculated using rule-based logic  
5. Insights and suggestions are generated  
6. Results are shown in the frontend  



## System Workflow

1. Upload contract  
2. Extract text  
3. Extract key values  
4. Calculate risk  
5. Generate insights  
6. Display results  



## API Endpoints

- `/analyze/` → Analyze contract  
- `/compare/` → Compare contracts  
- `/chat/` → Chat assistant  



## Technologies used

- Python  
- FastAPI  
- PyPDF2  
- Regex  
- HTML, CSS, JavaScript  



## How to run

### Step 1: Run backend
uvicorn main:app --reload

### Step 2: Open frontend
Open `index.html` in your browser


## What makes this project useful

- Makes complex contracts easy to understand  
- Saves time  
- Helps users make better decisions  
- Highlights hidden risks  



## Future improvements

- Use AI models for better understanding  
- Add real vehicle data using VIN  
- Improve chatbot intelligence  
- Build full mobile/web application  



## My contribution

- Designed the idea  
- Built backend logic  
- Created frontend UI  
- Implemented risk analysis system  
- Added chatbot functionality  

