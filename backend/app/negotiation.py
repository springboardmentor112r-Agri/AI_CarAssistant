"""
Negotiation Engine - Powered by Groq AI
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
logger.info("✅ Groq AI initialized successfully")


class NegotiationEngine:
    def __init__(self):
        self.chat_sessions: Dict[str, List[Dict]] = {}

    def _generate(self, prompt: str) -> Optional[str]:
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return None

    def _get_or_create_session(self, session_id: str) -> List[Dict]:
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = []
        return self.chat_sessions[session_id]

    def _build_conversation_prompt(self, system_prompt: str, history: List[Dict], user_message: str) -> str:
        prompt = system_prompt + "\n\n"
        for msg in history[-10:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt += f"{role}: {msg['content']}\n\n"
        prompt += f"User: {user_message}\n\nAssistant:"
        return prompt

    def generate_system_prompt(self, vehicle_details: Dict[str, Any], market_value: Dict[str, Any]) -> str:
        car_name = (
            f"{vehicle_details.get('year')} {vehicle_details.get('make')} "
            f"{vehicle_details.get('model')} {vehicle_details.get('trim', '')}"
        ).strip()
        fair_price = market_value.get("price", 0)
        currency = market_value.get("currency", "USD")

        return f"""You are an expert car negotiation assistant helping a buyer negotiate a better deal.

VEHICLE: {car_name}
FAIR MARKET VALUE: {currency} {fair_price:,.2f}

YOUR ROLE:
- Help the user get a deal at or below the fair market value
- Analyze dealer offers and identify overcharges
- Suggest counter-offers and negotiation tactics
- Explain lease terms when asked
- Be confident, professional, and encouraging

RULES:
- Keep responses concise (2-3 sentences max)
- Always reference the market data when discussing prices
- Suggest specific dollar amounts for counter-offers
- Warn about common dealer add-ons and fees"""

    def get_response(self, user_message: str, context: Optional[Dict[str, Any]] = None, session_id: str = "default") -> str:
        if not context:
            return "I need vehicle information first. Please enter a VIN to analyze the car you're interested in."

        vehicle_details = context.get("vehicle_details") or {}
        market_value = context.get("market_value") or {}

        if not vehicle_details or not market_value:
            return "I'm missing vehicle data. Let's start by analyzing the VIN."

        history = self._get_or_create_session(session_id)
        history.append({"role": "user", "content": user_message})

        system_prompt = self.generate_system_prompt(vehicle_details, market_value)
        full_prompt = self._build_conversation_prompt(system_prompt, history[:-1], user_message)
        response_text = self._generate(full_prompt)

        if not response_text:
            response_text = self._fallback_response(user_message, vehicle_details, market_value)

        history.append({"role": "assistant", "content": response_text})
        return response_text

    def get_chat_history(self, session_id: str = "default") -> List[Dict]:
        return self.chat_sessions.get(session_id, [])

    def clear_chat_history(self, session_id: str = "default"):
        if session_id in self.chat_sessions:
            self.chat_sessions[session_id] = []

    def analyze_document_text(self, text: str, user_prompt: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"analyze_document_text called - text length: {len(text)}, prompt: {user_prompt}")
        try:
            question = user_prompt or "Extract and summarize all key information."
            prompt = f"""You are a car negotiation expert analyzing a dealer document.

USER QUESTION: {question}

DOCUMENT TEXT:
{text[:4000]}

Tasks:
- Identify document type
- Extract: VIN, Year, Make, Model, Trim, Price, Fees
- Flag hidden fees and red flags
- Give negotiation advice"""

            response_text = self._generate(prompt)
            if response_text:
                return {"success": True, "response": response_text, "is_conversation": True}
            return {"success": False, "error": "No response from AI"}

        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            return {"success": False, "error": str(e)}

    def _fallback_response(self, user_message: str, vehicle_details: Dict, market_value: Dict) -> str:
        price = market_value.get("price", 0)
        msg = user_message.lower()
        if any(word in msg for word in ["offer", "price", "asking", "$"]):
            return f"Based on market data, the fair value is ${price:,.2f}. If they're asking more, mention you have pricing data and ask to see the invoice price."
        if "lease" in msg:
            return "For leasing, focus on the Money Factor (aim for 0.0015–0.0025) and Residual Value. Ask: 'What's the base money factor before any markup?'"
        return f"Your target is around ${price:,.2f}. Have they added any dealer accessories or protection packages you didn't request?"
