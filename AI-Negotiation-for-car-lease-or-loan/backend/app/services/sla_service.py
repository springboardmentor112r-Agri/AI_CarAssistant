import json
import re
import asyncio
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings


class SLAExtractionError(Exception):
    """Raised when SLA extraction fails due to a transient LLM error
    (rate limit, context window, network) that the user can retry."""
    def __init__(self, reason: str, detail: str = ""):
        self.reason = reason   # short key: rate_limit | context_window | network
        self.detail = detail   # human-readable message for frontend
        super().__init__(self.detail)

# ─── CORE FIELDS ──────────────────────────────────────────────────────
# At least ONE must be non-null for extraction to be considered
# successful. Without these the negotiation advice is meaningless.
CORE_FIELDS = [
    "monthly_payment",
    "apr",
    "lease_term",
    "down_payment",
]

# ─── EXTRACTION PROMPT ────────────────────────────────────────────────
EXTRACTION_SYSTEM_PROMPT = """
You are an expert car lease and loan contract analyst.
You have deep knowledge of both US and Indian automotive
financing markets.

Extract ALL contract terms from the document text provided.
The document may be a LEASE contract or a LOAN contract or both.

RULES:
- Return ONLY a valid JSON object.
- No explanation. No markdown. No preamble. No trailing text.
- If a field is not present in the document return null.
- red_flags must always be an array (empty [] if none).
- Extract values EXACTLY as written in the contract.
- For currency: preserve original symbol ($ or \u20b9).
- For percentages: preserve % symbol.

JSON SCHEMA:
{
  "contract_type": "lease or loan or null",

  "apr": "Annual Percentage Rate e.g. '5.9%' or null",
  "money_factor": "Lease money factor e.g. '0.00125' or null",
  "lease_term": "e.g. '36 months' or null",
  "loan_term": "e.g. '60 months' or null",
  "monthly_payment": "e.g. '$450/month' or '\u20b932,000/month' or null",
  "down_payment": "e.g. '$3,000' or '\u20b92,50,000' or null",

  "residual_value": "Lease only: end value e.g. '$18,000' or null",
  "mileage_allowance": "Lease only: e.g. '12,000 miles/year' or null",
  "mileage_overage_charge": "Lease only: e.g. '$0.20/mile' or null",
  "acquisition_fee": "Lease only: e.g. '$795' or null",
  "disposition_fee": "Lease only: e.g. '$350' or null",

  "loan_amount": "Loan only: principal e.g. '$25,000' or null",
  "prepayment_penalty": "Loan only: e.g. '$500' or 'None' or null",
  "balloon_payment": "Loan only: e.g. '$8,000' or 'None' or null",

  "early_termination_fee": "e.g. '$500' or '\u20b940,000' or null",
  "buyout_price": "e.g. '$20,000' or null",
  "maintenance_responsibility": "e.g. 'Lessee' or 'Dealer' or null",
  "warranty": "e.g. '3yr/36,000 miles' or null",
  "late_fee": "e.g. '$50' or null",
  "gap_coverage": "e.g. 'Included' or 'Not included' or null",
  "vin": "17-character VIN if present or null",

  "red_flags": [
    "array of strings \u2014 one string per red flag found"
  ]
}

RED FLAG CRITERIA:

LEASE RED FLAGS \u2014 add to red_flags if true:
  - APR > 7%:
      "High APR: {value} exceeds 7% market benchmark"
  - Money factor > 0.003 (equivalent ~7.2% APR):
      "High money factor: {value} \u2014 equivalent APR exceeds 7.2%"
  - Mileage overage > $0.20/mile or \u20b915/km:
      "High overage charge: {value} exceeds fair market rate"
  - GAP coverage not included:
      "No GAP coverage \u2014 you are financially exposed if car is totaled"
  - Early termination fee > $500 or \u20b940,000:
      "High early termination fee: {value}"
  - Residual value < 45% of any mentioned MSRP:
      "Low residual value: {value} \u2014 poor lease economics"
  - Acquisition fee > $800 or \u20b965,000:
      "High acquisition fee: {value}"
  - Disposition fee > $400 or \u20b933,000:
      "High disposition fee: {value}"
  - Auto-renew clause without written consent:
      "Auto-renewal clause found \u2014 requires written consent to cancel"

LOAN RED FLAGS \u2014 add to red_flags if true:
  - APR > 9% for new car:
      "High APR for new car: {value} exceeds 9% benchmark"
  - APR > 14% for used car:
      "High APR for used car: {value} exceeds 14% benchmark"
  - Prepayment penalty exists:
      "Prepayment penalty found: {value} \u2014 you will be charged for paying early"
  - Balloon payment clause:
      "Balloon payment found: {value} \u2014 large payment due at end of term"
  - Loan term > 72 months:
      "Long loan term: {value} \u2014 increases total interest paid significantly"
  - Negative equity clause:
      "Negative equity clause found \u2014 dealer can roll losses into new contract"
  - Mandatory dealer add-ons included in loan:
      "Mandatory add-ons found in loan \u2014 inflates principal unnecessarily"
"""

STRICT_JSON_REMINDER = """
Your previous response could not be parsed as JSON.
Return ONLY the JSON object.
No explanation. No markdown. No text before or after the JSON.
Start your response with { and end with }
"""


class SLAExtractorService:
    def __init__(self):
        # Primary: fast model with high free-tier rate limits
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=settings.GROQ_API_KEY,
            temperature=0,
            max_tokens=2000,
        )
        # Fallback: larger model if primary hits rate limit
        self.fallback_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            temperature=0,
            max_tokens=2000,
        )
        self._use_fallback = False

    # ─── EMPTY SLA TEMPLATE ────────────────────────────────────────────
    EMPTY_SLA = {
        "contract_type": None,
        "apr": None,
        "money_factor": None,
        "lease_term": None,
        "loan_term": None,
        "monthly_payment": None,
        "down_payment": None,
        "residual_value": None,
        "mileage_allowance": None,
        "mileage_overage_charge": None,
        "acquisition_fee": None,
        "disposition_fee": None,
        "loan_amount": None,
        "prepayment_penalty": None,
        "balloon_payment": None,
        "early_termination_fee": None,
        "buyout_price": None,
        "maintenance_responsibility": None,
        "warranty": None,
        "late_fee": None,
        "gap_coverage": None,
        "vin": None,
        "red_flags": [],
    }

    # ─── PUBLIC ENTRY POINT ───────────────────────────────────────────
    async def extract_sla(self, raw_extracted_text: str) -> dict:
        """
        GOLD STANDARD WORKFLOW.

        Attempt 1: Full text single LLM call
          Got valid JSON with core field? -> return immediately
          Got JSON but all core nulls?    -> try Attempt 2
          Got no JSON?                    -> try Attempt 2

        Attempt 2: Strict prompt reminder + retry
          Got valid JSON with core field? -> return immediately
          Still failed?                   -> try Attempt 3

        Attempt 3: Chunked extraction + merge
          Got valid JSON with core field? -> return merged result
          Still failed?                   -> return empty template

        Returns:
          dict  -> always returns a dict (empty template if nothing found)

        Raises:
          SLAExtractionError -> if ALL attempts fail due to transient LLM
            errors (rate limit, context window, network). The caller should
            set status='sla_failed' so the user can retry.
        """
        best_result = None
        last_transient_error = None

        # Reset fallback flag for each new extraction
        self._use_fallback = False
        hit_rate_limit = False

        # Attempt 1: Full text
        await asyncio.sleep(0)  # yield to event loop
        try:
            result = await self._attempt_full(raw_extracted_text)
            if result and self._has_core_field(result):
                return result
            if result:
                best_result = result
        except SLAExtractionError as e:
            last_transient_error = e
            if e.reason == "rate_limit":
                hit_rate_limit = True
            print(f"[SLA] Attempt 1 failed: {e.reason} — {e.detail}")

        # Delay: 10s after rate limit, 2s otherwise
        await asyncio.sleep(10 if hit_rate_limit else 2)

        # Attempt 2: Strict JSON reminder
        try:
            result = await self._attempt_strict(raw_extracted_text)
            if result and self._has_core_field(result):
                return result
            if result and not best_result:
                best_result = result
        except SLAExtractionError as e:
            last_transient_error = e
            if e.reason == "rate_limit":
                hit_rate_limit = True
            print(f"[SLA] Attempt 2 failed: {e.reason} — {e.detail}")

        # Delay: 15s after rate limit, 3s otherwise
        await asyncio.sleep(15 if hit_rate_limit else 3)

        # Attempt 3: Chunked extraction
        try:
            result = await self._attempt_chunked(raw_extracted_text)
            if result and self._has_core_field(result):
                return result
            if result and not best_result:
                best_result = result
        except SLAExtractionError as e:
            last_transient_error = e
            print(f"[SLA] Attempt 3 failed: {e.reason} — {e.detail}")

        # If we got partial results from any attempt, return them
        if best_result:
            return {**self.EMPTY_SLA, **best_result}

        # ALL attempts failed with NO usable result at all
        # If the cause was transient, raise so caller can set sla_failed
        if last_transient_error:
            raise last_transient_error

        # No transient error, just couldn't parse — return empty template
        return dict(self.EMPTY_SLA)

    # ─── ATTEMPT 1: FULL TEXT ─────────────────────────────────────────
    async def _attempt_full(self, text: str) -> dict | None:
        """
        Single LLM call with full contract text.
        Truncate at 9000 chars to stay safe.
        """
        messages = [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=f"CONTRACT DOCUMENT:\n\n{text[:9000]}")
        ]
        return await self._call_llm(messages)

    # ─── ATTEMPT 2: STRICT REMINDER ───────────────────────────────────
    async def _attempt_strict(self, text: str) -> dict | None:
        """
        Same text but with strict JSON reminder added.
        Handles cases where LLM added explanation or markdown.
        """
        messages = [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=f"CONTRACT DOCUMENT:\n\n{text[:9000]}"),
            HumanMessage(content=STRICT_JSON_REMINDER)
        ]
        return await self._call_llm(messages)

    # ─── ATTEMPT 3: CHUNKED ───────────────────────────────────────────
    async def _attempt_chunked(self, text: str) -> dict | None:
        """
        Split contract into chunks.
        Extract from each chunk separately.
        Merge results — first non-null wins per field.
        Union all red_flags.
        
        For large documents, only scan first 5 and last 2 chunks.
        """
        all_chunks = self._split_text(text, chunk_size=6000, overlap=300)
        
        # Limit to first 5 and last 2 chunks to avoid timeout on huge docs
        if len(all_chunks) > 7:
            chunks_to_process = all_chunks[:5] + all_chunks[-2:]
            print(f"[SLA] Large document ({len(all_chunks)} chunks). Scanning first 5 and last 2 chunks only.")
        else:
            chunks_to_process = all_chunks
            
        results = []

        for i, chunk in enumerate(chunks_to_process):
            if i > 0:
                await asyncio.sleep(2)
            
            print(f"[SLA] Scanning chunk {i+1}/{len(chunks_to_process)}...")
            # Yield progress info to caller if callback provided
            if hasattr(self, "_progress_callback") and self._progress_callback:
                await self._progress_callback(i + 1, len(chunks_to_process), f"Analyzing terms in section {i+1}/{len(chunks_to_process)}...")

            messages = [
                SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"This is part {i+1} of {len(chunks_to_process)} of a contract section scan.\n"
                        f"Extract whatever terms are present in this section.\n\n"
                        f"CONTRACT SECTION:\n\n{chunk}"
                    )
                )
            ]
            result = await self._call_llm(messages)
            if result:
                results.append(result)

        if not results:
            return None

        return self._merge_results(results)

    # ─── LLM CALL ─────────────────────────────────────────────────────
    async def _call_llm(self, messages: list) -> dict | None:
        """
        Single LLM call with JSON parsing.
        Returns dict if successful, None if JSON parse failed.
        Raises SLAExtractionError for transient LLM failures
        (rate limit, context window, network) so callers can retry.

        On rate-limit errors: retries once internally after 15s wait,
        switching to a smaller fallback model.
        """
        return await self._call_llm_inner(messages, retry_on_rate_limit=True)

    async def _call_llm_inner(
        self, messages: list, retry_on_rate_limit: bool = True
    ) -> dict | None:
        """Inner LLM call with optional rate-limit retry."""
        llm = self.fallback_llm if self._use_fallback else self.llm
        model_name = "fallback" if self._use_fallback else "primary"

        try:
            # 60-second timeout so it never hangs forever
            response = await asyncio.wait_for(
                llm.ainvoke(messages), timeout=60
            )
            raw = response.content.strip()

            # Strip markdown code fences if present
            raw = re.sub(r"```json|```", "", raw).strip()

            # Find JSON object in response
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not json_match:
                return None

            parsed = json.loads(json_match.group())
            return parsed

        except json.JSONDecodeError:
            return None
        except asyncio.TimeoutError:
            print(f"[SLA] LLM call timed out after 60s on {model_name} model")
            raise SLAExtractionError(
                reason="network",
                detail="AI analysis timed out. Please retry.",
            )
        except Exception as e:
            err = str(e).lower()
            if "rate limit" in err or "429" in err:
                if retry_on_rate_limit:
                    # Switch to fallback model and retry after 15s
                    self._use_fallback = True
                    print(
                        f"[SLA] Rate limit hit on {model_name} model, "
                        f"waiting 15s then retrying with fallback..."
                    )
                    await asyncio.sleep(15)
                    return await self._call_llm_inner(
                        messages, retry_on_rate_limit=False
                    )
                raise SLAExtractionError(
                    reason="rate_limit",
                    detail="LLM rate limit reached. Please retry in a moment.",
                )
            if "context" in err and ("length" in err or "window" in err or "too long" in err or "token" in err):
                raise SLAExtractionError(
                    reason="context_window",
                    detail="Document too large for analysis. Please retry — the system will use chunked processing.",
                )
            if any(kw in err for kw in ("timeout", "connection", "network", "unreachable", "503", "502")):
                raise SLAExtractionError(
                    reason="network",
                    detail="Network error reaching the AI service. Please retry.",
                )
            # Unknown error — still propagate so it doesn't silently become empty
            raise SLAExtractionError(
                reason="unknown",
                detail=f"Analysis failed: {str(e)[:150]}. Please retry.",
            )

    # ─── HELPERS ──────────────────────────────────────────────────────
    def _has_core_field(self, sla: dict) -> bool:
        return any(
            sla.get(field) is not None
            for field in CORE_FIELDS
        )

    def _split_text(
        self, text: str, chunk_size: int, overlap: int
    ) -> list[str]:
        chunks, start = [], 0
        while start < len(text):
            chunks.append(text[start:start + chunk_size])
            start += chunk_size - overlap
        return chunks

    def _merge_results(self, results: list[dict]) -> dict:
        """
        Merge extractions from multiple chunks.
        Scalar fields: first non-null value wins.
        red_flags: union of all arrays, deduplicated.
        """
        all_fields = [
            "contract_type", "apr", "money_factor", "lease_term",
            "loan_term", "monthly_payment", "down_payment",
            "residual_value", "mileage_allowance",
            "mileage_overage_charge", "acquisition_fee",
            "disposition_fee", "loan_amount", "prepayment_penalty",
            "balloon_payment", "early_termination_fee", "buyout_price",
            "maintenance_responsibility", "warranty", "late_fee",
            "gap_coverage", "vin"
        ]
        merged = {}
        for field in all_fields:
            merged[field] = next(
                (r[field] for r in results if r.get(field) is not None),
                None
            )
        all_flags = []
        for r in results:
            all_flags.extend(r.get("red_flags") or [])
        merged["red_flags"] = list(set(all_flags))
        return merged

    # ─── FAIRNESS SCORE ───────────────────────────────────────────────
    def compute_fairness_score(self, sla: dict) -> float:
        """
        Weighted scoring 0-100.
        Weights:
          APR / Money Factor   25 pts
          Overage charge       20 pts
          GAP coverage         20 pts
          Early term fee       15 pts
          Red flags count      20 pts
        """
        score = 0.0

        # APR Score (25 pts)
        apr = self._parse_float(sla.get("apr") or "")
        mf  = self._parse_float(sla.get("money_factor") or "")
        if apr is None and mf is not None:
            apr = mf * 2400  # money factor to APR conversion
        if apr is None:      score += 12
        elif apr <= 4:       score += 25
        elif apr <= 7:       score += 18
        elif apr <= 9:       score += 10
        elif apr <= 14:      score += 4
        else:                score += 0

        # Overage Charge Score (20 pts)
        ovg = self._parse_float(sla.get("mileage_overage_charge") or "")
        if ovg is None:      score += 10
        elif ovg <= 0.10:    score += 20
        elif ovg <= 0.15:    score += 15
        elif ovg <= 0.20:    score += 8
        elif ovg <= 0.25:    score += 3
        else:                score += 0

        # GAP Coverage Score (20 pts)
        gap = (sla.get("gap_coverage") or "").lower()
        if "included" in gap or "yes" in gap:  score += 20
        elif not gap:                          score += 10
        else:                                  score += 0

        # Early Termination Score (15 pts)
        etf = self._parse_float(sla.get("early_termination_fee") or "")
        if etf is None:      score += 7
        elif etf <= 200:     score += 15
        elif etf <= 500:     score += 9
        elif etf <= 1000:    score += 3
        else:                score += 0

        # Red Flags Score (20 pts)
        flags = len(sla.get("red_flags") or [])
        if flags == 0:       score += 20
        elif flags == 1:     score += 14
        elif flags == 2:     score += 8
        elif flags == 3:     score += 3
        else:                score += 0

        return round(score, 1)

    def _parse_float(self, value: str) -> float | None:
        try:
            cleaned = re.sub(r"[^\d.]", "", str(value))
            parts = cleaned.split(".")
            if len(parts) > 2:
                cleaned = parts[0] + "." + "".join(parts[1:])
            return float(cleaned) if cleaned else None
        except Exception:
            return None


# Singleton instance
sla_service = SLAExtractorService()
