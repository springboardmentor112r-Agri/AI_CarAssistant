# chatbot.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
router = APIRouter(prefix="/chat")

class ChatRequest(BaseModel):
    message: str
    contract_text: str | None = ""

@router.post("/message")
async def chat(data: ChatRequest):
    try:
        message = data.message
        contract_text = data.contract_text or ""

        prompt = f"""
You are "LeaseGuard AI," a high-stakes automotive contract negotiator. 
Your goal is to help the user find hidden costs and negotiate better terms.

CONTRACT DATA:
{contract_text[:8000]}

USER REQUEST: {message}

INSTRUCTIONS:
1. If the user asks about risk, identify specific clauses.
2. Always provide a "Negotiation Script".
3. Be firm and professional.
4. If no contract is provided, ask them to upload one.

RESPONSE FORMAT:
- **Analysis**:
- **The Catch**:
- **Negotiation Script**:
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )

        answer = response.choices[0].message.content.strip() # pyright: ignore[reportOptionalMemberAccess]
        return {"reply": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))