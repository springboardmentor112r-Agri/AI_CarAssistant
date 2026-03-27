# redflags.py
import os
from groq import Groq
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def detect_red_flags(text: str):
    prompt = f"List risky clauses in this contract:\n{text}"

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip() # pyright: ignore[reportOptionalMemberAccess]