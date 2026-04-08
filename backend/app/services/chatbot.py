import os
from openai import AsyncOpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

MOCK_RESPONSES = [
    "Based on your contract, I'd recommend negotiating the APR down first — even 1% reduction on a 36-month lease saves you hundreds. Ask the dealer: \"What's the best rate you can offer for a customer with my credit profile?\"",
    "The mileage allowance in your contract looks standard. If you drive more than average, consider negotiating for 15,000 miles/year upfront — it's cheaper than paying overage charges later.",
    "For the buyout price, compare it against current market listings on Edmunds or KBB. If the residual is above market value, you have strong negotiating leverage — the dealer wants you to buy it out.",
    "A good negotiation email to your dealer might be: \"I've reviewed the contract terms and would like to discuss adjusting the APR and monthly payment. I have competing offers from [Dealer X] and would prefer to finalize with you if we can reach a fair agreement.\"",
    "Red flags in lease contracts often include vague 'disposition fees', excessive wear-and-tear clauses, and overage charges above $0.25/mile. Always ask for these to be capped or removed before signing.",
]

_mock_index = 0

async def generate_negotiation_reply(contract_summary: dict, chat_history: list, new_user_message: str) -> str:
    """
    Generates a negotiation reply using OpenAI GPT.
    Falls back to helpful mock responses if OPENAI_API_KEY is not set.
    """
    global _mock_index

    if not client:
        print("[Chatbot] No OPENAI_API_KEY found — using mock negotiation response.")
        response = MOCK_RESPONSES[_mock_index % len(MOCK_RESPONSES)]
        _mock_index += 1
        return response

    system_prompt = f"""
    You are an expert automotive lease and loan negotiation assistant.
    Your goal is to help the user get the best possible deal based on the contract they uploaded.
    Be concise, professional, and practical. Suggest specific scripts or questions they can ask the dealer.
    
    --- CONTRACT SUMMARY CONTEXT ---
    APR: {contract_summary.get('apr', 'Unknown')}%
    Monthly Payment: ${contract_summary.get('monthly_payment', 'Unknown')}
    Term: {contract_summary.get('lease_term_months', 'Unknown')} months
    Residual Value: ${contract_summary.get('residual_value', 'Unknown')}
    Mileage Allowance: {contract_summary.get('mileage_allowance', 'Unknown')} miles/yr
    Red Flags: {', '.join(contract_summary.get('red_flags', []))}
    Fairness Score: {contract_summary.get('fairness_score', 'Unknown')}/100
    --------------------------------
    """

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-10:]:
        messages.append({
            "role": "user" if msg["role"] == "USER" else "assistant",
            "content": msg["content"]
        })
    messages.append({"role": "user", "content": new_user_message})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content or "I'm having trouble providing advice right now."
    except Exception as e:
        print(f"[Chatbot] Error calling OpenAI: {e} — using fallback response.")
        response = MOCK_RESPONSES[_mock_index % len(MOCK_RESPONSES)]
        _mock_index += 1
        return response
