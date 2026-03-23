"""
Negotiation chatbot service.

FLOW PER MESSAGE:
  STEP A — Get document from DB

  STEP B — Smart routing (dynamic RAG decision)
    1. Trivial messages (hi, thanks) → skip RAG entirely
    2. LLM intent classifier decides GENERAL vs DOCUMENT:
       GENERAL  → LLM answers from its own knowledge, NO Qdrant
       DOCUMENT → embed + retrieve from Qdrant (contract-specific)

  STEP C — (If DOCUMENT) Initialize vectors & retrieve chunks
    Check Qdrant: thread_id vectors exist?
    NO  -> embed_and_store (lazy, only on first message)
    YES -> skip
    Search Qdrant filtered by thread_id, get top 5 chunks

  STEP D — Get chat history from Neon
    SELECT last 10 messages WHERE thread_id = X

  STEP E — Assemble LLM context
    System: negotiation persona + sla_json + fairness score
    Retrieved chunks: relevant contract sections (if any)
    History: last 10 messages
    User: current message

  STEP F — Stream from Groq

  STEP G — Persist to Neon
    Save user message + full assistant reply
"""

import json
import asyncio
import logging
from uuid import UUID
from langchain_groq import ChatGroq
from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.models.models import ChatHistory
from app.services.document_service import get_document_for_chat
from app.services.vector_service import vector_service
from app.core.config import settings
from app.services.llm_logger import (
  log_llm_call, estimate_tokens, LLMCallTimer
)
from app.services.document_service import get_document_with_text

logger = logging.getLogger(__name__)

NEGOTIATION_SYSTEM_PROMPT = """
You are an expert car lease and loan negotiation coach
with deep knowledge of US and Indian automotive markets.

Your job is to help the user understand, analyse, and
negotiate their car contract to get the best possible deal.

CONTRACT TERMS EXTRACTED FROM DOCUMENT:
─────────────────────────────────────────
{sla_json_formatted}
─────────────────────────────────────────

CONTRACT FAIRNESS SCORE: {fairness_score}/100
{fairness_context}

{rag_section}

YOUR BEHAVIOR:
- Format ALL responses in clean markdown
- Use ## for section headings (not bold text)
- Use **bold** ONLY for numbers, fees, percentages
  Example: **18% APR**, **$425/month**
  NOT for entire sentences or paragraphs
- Normal text must be plain weight (not bold)
- Use bullet points (-) for lists
- Use numbered lists for steps
- Use > blockquote for dealer scripts ONLY
- NEVER make entire paragraphs bold
- NEVER bold normal explanatory sentences
- Structure every response:

    ## Summary
    2-3 plain sentences. No bold except numbers.

    ## Issues Found
    - Issue one (**18% APR** exceeds benchmark)
    - Issue two (no GAP coverage)

    ## What You Can Do
    1. Step one
    2. Step two

    ## What To Say
    > "Exact script to say to dealer"

- Keep responses concise and readable
- If no issues: skip Issues Found section
- If no negotiation needed: skip What To Say
- If user asks general car buying question:
    answer helpfully without forcing structure
- If user asks to write email:
    write complete email with subject line in a code block
- If term not in contract:
    state clearly "This term was not found in your contract"
- For legal questions:
    recommend consulting a licensed attorney
- Never make up contract terms not in the document
"""

# Simple messages that need NO vector search AND no classification
# Pure conversation — no contract context needed
SIMPLE_INTENTS = {
  # Acknowledgements
  "ok", "okay", "ok done", "got it", "understood",
  "thanks", "thank you", "thx", "ty",
  # Greetings
  "hi", "hello", "hey", "good morning",
  "good afternoon", "good evening",
  # Farewells
  "bye", "goodbye", "see you", "cya", "done",
  "exit", "quit",
  # Affirmations
  "yes", "no", "sure", "alright", "fine",
  "great", "perfect", "nice", "good",
  # Short reactions
  "wow", "interesting", "hmm", "ok thanks",
  "noted", "i see", "i understand",
}

def is_simple_message(message: str) -> bool:
  """
  Returns True for trivial conversational messages
  (greetings, acknowledgements) that need NO LLM
  classification and NO vector search.
  """
  msg_clean = message.lower().strip().rstrip('.,!?')
  if msg_clean in SIMPLE_INTENTS:
    return True
  # Very short non-question messages
  words = msg_clean.split()
  if len(words) <= 2 and '?' not in message:
    return True
  return False


INTENT_CLASSIFIER_PROMPT = """You are a routing classifier for a car lease/loan negotiation chatbot.
The user has uploaded their specific contract document. Decide whether
the user's message requires looking up their CONTRACT DOCUMENT or can
be answered from general knowledge alone.

Respond with EXACTLY one word:
  DOCUMENT — if the answer depends on the user's specific contract,
             their specific numbers, clauses, or terms in their deal.
  GENERAL  — if the question is about general concepts, definitions,
             industry knowledge, or advice that does NOT need the
             user's specific contract data.

Examples:
  "What is APR?" → GENERAL
  "What is my APR?" → DOCUMENT
  "How does gap insurance work?" → GENERAL
  "Do I have gap insurance?" → DOCUMENT
  "What is a good interest rate for a car loan?" → GENERAL
  "Is my interest rate too high?" → DOCUMENT
  "Explain early termination fee" → GENERAL
  "What is my early termination penalty?" → DOCUMENT
  "Tips for negotiating a car lease" → GENERAL
  "What should I negotiate in my contract?" → DOCUMENT
  "What does amortization mean?" → GENERAL
  "Show me the payment schedule" → DOCUMENT
  "What are typical lease mileage limits?" → GENERAL
  "What is my mileage limit?" → DOCUMENT

User message: {message}
"""


async def classify_intent(llm, message: str) -> str:
  """
  Use a fast LLM call to decide if the user's question
  needs document context (DOCUMENT) or can be answered
  from general knowledge (GENERAL).
  """
  try:
    prompt = INTENT_CLASSIFIER_PROMPT.format(message=message)
    response = await llm.ainvoke(
      [HumanMessage(content=prompt)],
    )
    answer = response.content.strip().upper()
    if "GENERAL" in answer:
      return "GENERAL"
    return "DOCUMENT"
  except Exception as e:
    logger.exception("[Chat] Intent classification failed")
    # Default to DOCUMENT so we never lose contract context
    return "DOCUMENT"

FAIRNESS_CONTEXT = {
    "high":   "This is a FAIR contract (score 80-100). "
              "Minor improvements may still be possible.",
    "medium": "This contract has SOME CONCERNS (score 50-79). "
              "Several terms worth negotiating.",
    "low":    "This contract has SERIOUS ISSUES (score 0-49). "
              "Multiple unfavorable terms need attention.",
}

class ChatService:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            temperature=0.3,
            max_tokens=1500,
        )
        # Lightweight LLM for fast intent classification
        self.classifier_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            temperature=0,
            max_tokens=10,
        )

    # ─── GET HISTORY ─────────────────────────────────────────
    async def get_chat_history(
        self,
        db: AsyncSession,
        thread_id: UUID,
        limit: int = 10
    ) -> list:
        result = await db.execute(
            select(ChatHistory)
            .where(ChatHistory.thread_id == thread_id)
            .order_by(ChatHistory.timestamp.asc())
            .limit(limit)
        )
        return result.scalars().all()

    # ─── SAVE MESSAGE ────────────────────────────────────────
    async def save_message(
        self,
        db: AsyncSession,
        thread_id: UUID,
        doc_id: UUID,
        user_id: UUID,
        role: str,
        content: str,
    ) -> None:
        """
        Save a single chat message to chat_history.
        Called TWICE per conversation turn:
          1. User message (before streaming)
          2. Assistant message (after streaming)
        """
        msg = ChatHistory(
            thread_id=thread_id,
            doc_id=doc_id,
            user_id=user_id,
            role=role,
            content=content,
        )
        db.add(msg)
        await db.commit()

    # ─── HELPERS ─────────────────────────────────────────────
    def _build_system_prompt(
        self,
        sla_json: dict,
        fairness_score: float,
        chunks: list[str],
    ) -> str:
        if fairness_score >= 80:
            fairness_context = FAIRNESS_CONTEXT["high"]
        elif fairness_score >= 50:
            fairness_context = FAIRNESS_CONTEXT["medium"]
        else:
            fairness_context = FAIRNESS_CONTEXT["low"]

        if chunks:
            rag_section = "\nRELEVANT CONTRACT SECTIONS:\n"
            rag_section += "─────────────────────────────────────────\n"
            rag_section += "\n---\n".join(chunks)
            rag_section += "\n─────────────────────────────────────────\n"
        else:
            rag_section = ""

        return NEGOTIATION_SYSTEM_PROMPT.format(
            sla_json_formatted=json.dumps(sla_json, indent=2),
            fairness_score=fairness_score,
            fairness_context=fairness_context,
            rag_section=rag_section,
        )

    def _build_lc_messages(
        self,
        system_content: str,
        history: list,
        user_message: str,
    ) -> list:
        lc_messages = [SystemMessage(content=system_content)]
        for row in history:
            if row.role == "user":
                lc_messages.append(HumanMessage(content=row.content))
            else:
                lc_messages.append(AIMessage(content=row.content))
        lc_messages.append(HumanMessage(content=user_message))
        return lc_messages

    # ─── MAIN STREAM ─────────────────────────────────────────
    async def stream_message(
        self,
        db: AsyncSession,
        user_id: UUID,
        doc_id: UUID,
        thread_id: UUID,
        user_message: str,
    ):
        """
        Stream LLM response token by token to frontend.
        Save user message + full assistant reply to DB
        ONCE after stream completes.
        Never save inside the streaming loop.
        """

        # ── STEP A: Get document ─────────────────────────
        document = await get_document_with_text(
            db, doc_id, user_id
        )
        if not document:
            yield "[ERROR]document not found"
            return

        # ── STEP B: Smart routing ──────────────────────────
        # Dynamically decide whether to query vector DB:
        #   1. Trivial messages (hi, thanks) → skip entirely
        #   2. General knowledge questions → LLM answers directly
        #   3. Document-specific questions → use RAG

        chunks = []

        if is_simple_message(user_message):
          use_rag = False
          logger.info("[Chat] Simple message detected; skipping RAG")
        else:
          intent = await classify_intent(
            self.classifier_llm, user_message
          )
          use_rag = (intent == "DOCUMENT")
          logger.info(
            "[Chat] Intent=%s; %s RAG",
            intent,
            "using" if use_rag else "skipping",
          )

        if use_rag:
          # Initialize vectors (lazy)
          try:
            await vector_service.ensure_vectors(
              document=document,
              user_id=str(user_id),
              doc_id=str(doc_id),
              thread_id=str(thread_id),
            )
          except Exception:
            logger.exception("[Chat] Vector initialization failed")

          # Retrieve relevant chunks
          try:
            chunks = vector_service.retrieve(
              query=user_message,
              thread_id=str(thread_id),
              top_k=5,
            )
          except Exception:
            logger.exception("[Chat] Vector retrieval failed")
            chunks = []

        # ── STEP D: Get last 10 messages from history ────
        history = await self.get_chat_history(
            db, thread_id, limit=10
        )

        # ── STEP E: Build prompt ──────────────────────────
        sla_json = document.sla_json or {}
        fairness = document.contract_fairness_score or 0

        system_content = self._build_system_prompt(
            sla_json=sla_json,
            fairness_score=fairness,
            chunks=chunks,
        )

        lc_messages = self._build_lc_messages(
            system_content=system_content,
            history=history,
            user_message=user_message,
        )

        # ── STEP F: Save user message BEFORE streaming ───
        await self.save_message(
            db=db,
            thread_id=thread_id,
            doc_id=doc_id,
            user_id=user_id,
            role="user",
            content=user_message,
        )

        # ── STEP G: Stream from LLM ───────────────────────
        prompt_tokens = estimate_tokens(
            system_content + " ".join(m.content for m in lc_messages)
        )
        stream_timer = LLMCallTimer()
        stream_timer.start()

        full_reply = ""
        max_retries = 2
        retry_count = 0

        while retry_count <= max_retries:
            try:
                async for chunk in self.llm.astream(lc_messages):
                    token = chunk.content
                    if token:
                        full_reply += token
                        yield token
                
                # Log successful chat call
                elapsed = stream_timer.stop()
                completion_tokens = estimate_tokens(full_reply)
                await log_llm_call(
                    module="chat",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    response_time_ms=elapsed,
                    success=True,
                    user_id=user_id,
                    doc_id=doc_id,
                    thread_id=thread_id,
                )
                break

            except Exception as e:
                error_str = str(e).lower()
                if "rate limit" in error_str or "429" in error_str:
                    retry_count += 1
                    if retry_count <= max_retries:
                        await asyncio.sleep(3 * retry_count)
                        full_reply = ""
                        continue
                
                elapsed = stream_timer.stop()
                await log_llm_call(
                    module="chat",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=estimate_tokens(full_reply),
                    response_time_ms=elapsed,
                    success=False,
                    error_message=str(e)[:200],
                    user_id=user_id,
                    doc_id=doc_id,
                    thread_id=thread_id,
                )
                raise

        # ── STEP H: Save assistant reply ONCE ────────────
        if full_reply:
            await self.save_message(
                db=db,
                thread_id=thread_id,
                doc_id=doc_id,
                user_id=user_id,
                role="assistant",
                content=full_reply,
            )

# Singleton instance
chat_service = ChatService()
