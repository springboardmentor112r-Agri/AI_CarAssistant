"""
LLM call logger service.
Logs every LLM call to Neon llm_logs table.
Used by sla_service, chat_service, vin_service.

GROQ PRICING (llama3-70b-8192):
  Input:  $0.00059 per 1K tokens
  Output: $0.00079 per 1K tokens
"""

import time
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date, Integer
from app.models.models import LLMLog
from app.core import database

MODEL_NAME = "llama-3.3-70b-versatile"
INPUT_COST_PER_1K  = 0.00059
OUTPUT_COST_PER_1K = 0.00079

def estimate_tokens(text: str) -> int:
  """
  Rough token estimate: 1 token ≈ 4 characters.
  Used when exact token count not available.
  """
  if not text:
      return 0
  return max(1, len(text) // 4)

def calculate_cost(
  prompt_tokens: int,
  completion_tokens: int
) -> float:
  """
  Calculate cost estimate in USD.
  Based on Groq llama3-70b-8192 pricing.
  """
  input_cost  = (prompt_tokens / 1000) * INPUT_COST_PER_1K
  output_cost = (completion_tokens / 1000) * OUTPUT_COST_PER_1K
  return round(input_cost + output_cost, 8)

class LLMCallTimer:
  """
  Context manager for timing LLM calls.

  Usage:
    timer = LLMCallTimer()
    timer.start()
    result = await llm.invoke(...)
    elapsed_ms = timer.stop()
  """
  def __init__(self):
    self._start = None

  def start(self):
    self._start = time.monotonic()

  def stop(self) -> int:
    if self._start is None:
      return 0
    return int((time.monotonic() - self._start) * 1000)

async def log_llm_call(
  module: str,
  prompt_tokens: int,
  completion_tokens: int,
  response_time_ms: int,
  success: bool,
  user_id: UUID | None = None,
  doc_id: UUID | None = None,
  thread_id: UUID | None = None,
  error_message: str | None = None,
):
  """
  Log a single LLM call to Neon.
  Creates its own DB session — safe to call from
  background tasks, streaming generators, and
  sync-wrapped async functions.
  """
  try:
    total = prompt_tokens + completion_tokens
    cost = calculate_cost(prompt_tokens, completion_tokens)

    async with database.AsyncSessionLocal() as db:
      try:
        log = LLMLog(
          user_id=user_id,
          doc_id=doc_id,
          thread_id=thread_id,
          module=module,
          model=MODEL_NAME,
          prompt_tokens=prompt_tokens,
          completion_tokens=completion_tokens,
          total_tokens=total,
          response_time_ms=response_time_ms,
          success=success,
          error_message=error_message,
          cost_estimate_usd=cost,
        )
        db.add(log)
        await db.commit()
      except Exception:
        await db.rollback()
        raise
      finally:
        await db.close()
  except Exception as e:
    # Never let logging break main flow
    print(f"[LLM Logger] Failed to log: {e}")

# ─── DASHBOARD QUERIES ───────────────────────────────────

async def get_overall_stats() -> dict:
  """
  Overall system stats for admin dashboard.
  Returns totals across all users and modules.
  """
  async with database.AsyncSessionLocal() as db:
    result = await db.execute(
      select(
        func.count(LLMLog.log_id).label("total_calls"),
        func.sum(LLMLog.total_tokens).label("total_tokens"),
        func.sum(LLMLog.cost_estimate_usd).label("total_cost"),
        func.avg(LLMLog.response_time_ms).label("avg_response_ms"),
        func.sum(
          cast(LLMLog.success == False, Integer)
        ).label("total_errors"),
      )
    )
    row = result.one()
    return {
      "total_calls":      int(row.total_calls or 0),
      "total_tokens":     int(row.total_tokens or 0),
      "total_cost_usd":   round(float(row.total_cost or 0), 6),
      "avg_response_ms":  int(row.avg_response_ms or 0),
      "total_errors":     int(row.total_errors or 0),
      "success_rate":     round(
        (1 - (row.total_errors or 0) / max(row.total_calls or 1, 1)) * 100,
        1
      ),
    }

async def get_daily_stats(days: int = 7) -> list:
  """
  Daily breakdown for the last N days.
  Used for the calls-over-time chart.
  """
  async with database.AsyncSessionLocal() as db:
    result = await db.execute(
      select(
        cast(LLMLog.timestamp, Date).label("date"),
        func.count(LLMLog.log_id).label("calls"),
        func.sum(LLMLog.total_tokens).label("tokens"),
        func.sum(LLMLog.cost_estimate_usd).label("cost"),
      )
      .group_by(cast(LLMLog.timestamp, Date))
      .order_by(cast(LLMLog.timestamp, Date).desc())
      .limit(days)
    )
    rows = result.all()
    return [
      {
        "date":   str(row.date),
        "calls":  int(row.calls or 0),
        "tokens": int(row.tokens or 0),
        "cost":   round(float(row.cost or 0), 6),
      }
      for row in reversed(rows)
    ]

async def get_module_stats() -> list:
  """
  Per module breakdown.
  Shows which module uses most tokens/calls.
  """
  async with database.AsyncSessionLocal() as db:
    result = await db.execute(
      select(
        LLMLog.module,
        func.count(LLMLog.log_id).label("calls"),
        func.sum(LLMLog.total_tokens).label("tokens"),
        func.avg(LLMLog.response_time_ms).label("avg_ms"),
        func.sum(
          cast(LLMLog.success == False, Integer)
        ).label("errors"),
      )
      .group_by(LLMLog.module)
      .order_by(func.count(LLMLog.log_id).desc())
    )
    rows = result.all()
    return [
      {
        "module":   row.module,
        "calls":    int(row.calls or 0),
        "tokens":   int(row.tokens or 0),
        "avg_ms":   int(row.avg_ms or 0),
        "errors":   int(row.errors or 0),
      }
      for row in rows
    ]

async def get_recent_logs(limit: int = 20) -> list:
  """
  Most recent LLM calls.
  Shows in admin log table.
  """
  async with database.AsyncSessionLocal() as db:
    result = await db.execute(
      select(LLMLog)
      .order_by(LLMLog.timestamp.desc())
      .limit(limit)
    )
    rows = result.scalars().all()
    return [
      {
        "log_id":          str(row.log_id),
        "timestamp":       row.timestamp.isoformat(),
        "module":          row.module,
        "model":           row.model,
        "prompt_tokens":   row.prompt_tokens,
        "completion_tokens": row.completion_tokens,
        "total_tokens":    row.total_tokens,
        "response_time_ms": row.response_time_ms,
        "success":         row.success,
        "error_message":   row.error_message,
        "cost_usd":        row.cost_estimate_usd,
        "user_id":         str(row.user_id) if row.user_id else None,
        "doc_id":          str(row.doc_id) if row.doc_id else None,
      }
      for row in rows
    ]

async def get_user_stats(user_id: UUID) -> dict:
  """
  Per user stats.
  Shown on user's own profile or admin view.
  """
  async with database.AsyncSessionLocal() as db:
    result = await db.execute(
      select(
        func.count(LLMLog.log_id).label("total_calls"),
        func.sum(LLMLog.total_tokens).label("total_tokens"),
        func.sum(LLMLog.cost_estimate_usd).label("total_cost"),
      )
      .where(LLMLog.user_id == user_id)
    )
    row = result.one()
    return {
      "total_calls":  int(row.total_calls or 0),
      "total_tokens": int(row.total_tokens or 0),
      "total_cost":   round(float(row.total_cost or 0), 6),
    }


# ─── EXTENDED ADMIN QUERIES ─────────────────────────────

from app.models.models import User, Document, ChatHistory

async def get_all_users_stats() -> list:
  """All users with their document counts and LLM usage."""
  async with database.AsyncSessionLocal() as db:
    # Subquery: per-user LLM stats
    llm_sub = (
      select(
        LLMLog.user_id,
        func.count(LLMLog.log_id).label("llm_calls"),
        func.coalesce(func.sum(LLMLog.total_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(LLMLog.cost_estimate_usd), 0).label("total_cost"),
      )
      .group_by(LLMLog.user_id)
      .subquery()
    )

    # Subquery: per-user document count
    doc_sub = (
      select(
        Document.user_id,
        func.count(Document.doc_id).label("doc_count"),
      )
      .group_by(Document.user_id)
      .subquery()
    )

    # Subquery: per-user chat message count
    chat_sub = (
      select(
        ChatHistory.user_id,
        func.count(ChatHistory.message_id).label("chat_count"),
      )
      .where(ChatHistory.role == "user")
      .group_by(ChatHistory.user_id)
      .subquery()
    )

    result = await db.execute(
      select(
        User.user_id,
        User.email,
        User.full_name,
        User.created_at,
        User.is_active,
        func.coalesce(doc_sub.c.doc_count, 0).label("doc_count"),
        func.coalesce(chat_sub.c.chat_count, 0).label("chat_count"),
        func.coalesce(llm_sub.c.llm_calls, 0).label("llm_calls"),
        func.coalesce(llm_sub.c.total_tokens, 0).label("total_tokens"),
        func.coalesce(llm_sub.c.total_cost, 0).label("total_cost"),
      )
      .outerjoin(doc_sub, User.user_id == doc_sub.c.user_id)
      .outerjoin(chat_sub, User.user_id == chat_sub.c.user_id)
      .outerjoin(llm_sub, User.user_id == llm_sub.c.user_id)
      .order_by(User.created_at.desc())
    )
    rows = result.all()
    return [
      {
        "user_id":     str(r.user_id),
        "email":       r.email,
        "full_name":   r.full_name,
        "created_at":  r.created_at.isoformat() if r.created_at else None,
        "is_active":   r.is_active,
        "doc_count":   int(r.doc_count),
        "chat_count":  int(r.chat_count),
        "llm_calls":   int(r.llm_calls),
        "total_tokens": int(r.total_tokens),
        "total_cost":  round(float(r.total_cost), 6),
      }
      for r in rows
    ]


async def get_documents_overview() -> list:
  """All documents with owner email and status."""
  async with database.AsyncSessionLocal() as db:
    result = await db.execute(
      select(
        Document.doc_id,
        Document.filename,
        Document.processing_status,
        Document.contract_fairness_score,
        Document.vin,
        Document.upload_timestamp,
        Document.sla_retry_count,
        Document.error_message,
        User.email.label("user_email"),
      )
      .join(User, Document.user_id == User.user_id)
      .order_by(Document.upload_timestamp.desc())
      .limit(200)
    )
    rows = result.all()
    return [
      {
        "doc_id":          str(r.doc_id),
        "filename":        r.filename,
        "status":          r.processing_status,
        "fairness_score":  r.contract_fairness_score,
        "vin":             r.vin,
        "uploaded_at":     r.upload_timestamp.isoformat() if r.upload_timestamp else None,
        "retry_count":     r.sla_retry_count,
        "error":           r.error_message,
        "user_email":      r.user_email,
      }
      for r in rows
    ]


async def get_document_status_counts() -> dict:
  """Count of documents per processing status."""
  async with database.AsyncSessionLocal() as db:
    result = await db.execute(
      select(
        Document.processing_status,
        func.count(Document.doc_id).label("count"),
      )
      .group_by(Document.processing_status)
    )
    rows = result.all()
    return {r.processing_status: int(r.count) for r in rows}


async def get_system_health() -> dict:
  """System health metrics: user counts, document pipeline, error rates."""
  async with database.AsyncSessionLocal() as db:
    # Total users
    user_count = (await db.execute(
      select(func.count(User.user_id))
    )).scalar() or 0

    # Active users (uploaded or chatted in last 7 days)
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    active_uploaders = (await db.execute(
      select(func.count(func.distinct(Document.user_id)))
      .where(Document.upload_timestamp >= cutoff)
    )).scalar() or 0

    # Total documents
    total_docs = (await db.execute(
      select(func.count(Document.doc_id))
    )).scalar() or 0

    # Documents in error/failed states
    error_docs = (await db.execute(
      select(func.count(Document.doc_id))
      .where(Document.processing_status.in_(["error", "sla_failed"]))
    )).scalar() or 0

    # Total chat messages
    total_chats = (await db.execute(
      select(func.count(ChatHistory.message_id))
    )).scalar() or 0

    # LLM error rate last 24h
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    llm_24h = (await db.execute(
      select(
        func.count(LLMLog.log_id).label("total"),
        func.sum(cast(LLMLog.success == False, Integer)).label("errors"),
      )
      .where(LLMLog.timestamp >= cutoff_24h)
    )).one()

    return {
      "total_users":       int(user_count),
      "active_users_7d":   int(active_uploaders),
      "total_documents":   int(total_docs),
      "error_documents":   int(error_docs),
      "total_chat_messages": int(total_chats),
      "llm_calls_24h":     int(llm_24h.total or 0),
      "llm_errors_24h":    int(llm_24h.errors or 0),
      "llm_error_rate_24h": round(
        (float(llm_24h.errors or 0) / max(float(llm_24h.total or 1), 1)) * 100, 1
      ),
    }


async def get_hourly_stats(hours: int = 24) -> list:
  """Hourly LLM call breakdown for the last N hours."""
  from datetime import timedelta
  cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
  async with database.AsyncSessionLocal() as db:
    result = await db.execute(
      select(
        func.date_trunc('hour', LLMLog.timestamp).label("hour"),
        func.count(LLMLog.log_id).label("calls"),
        func.sum(LLMLog.total_tokens).label("tokens"),
        func.sum(cast(LLMLog.success == False, Integer)).label("errors"),
      )
      .where(LLMLog.timestamp >= cutoff)
      .group_by(func.date_trunc('hour', LLMLog.timestamp))
      .order_by(func.date_trunc('hour', LLMLog.timestamp))
    )
    rows = result.all()
    return [
      {
        "hour":   r.hour.isoformat() if r.hour else None,
        "calls":  int(r.calls or 0),
        "tokens": int(r.tokens or 0),
        "errors": int(r.errors or 0),
      }
      for r in rows
    ]


async def get_fairness_score_distribution() -> list:
  """Distribution of fairness scores across all documents."""
  async with database.AsyncSessionLocal() as db:
    result = await db.execute(
      select(
        func.width_bucket(
          Document.contract_fairness_score, 0, 100, 10
        ).label("bucket"),
        func.count(Document.doc_id).label("count"),
      )
      .where(Document.contract_fairness_score.isnot(None))
      .group_by("bucket")
      .order_by("bucket")
    )
    rows = result.all()
    buckets = []
    for r in rows:
      b = int(r.bucket)
      low = max(0, (b - 1) * 10)
      high = min(100, b * 10)
      buckets.append({
        "range": f"{low}-{high}",
        "count": int(r.count),
      })
    return buckets


async def get_recent_activity(limit: int = 30) -> list:
  """Recent platform activity: uploads, chats, errors."""
  from sqlalchemy import union_all, literal_column, literal

  async with database.AsyncSessionLocal() as db:
    # Recent uploads
    uploads = (
      select(
        Document.upload_timestamp.label("ts"),
        literal("upload").label("type"),
        User.email.label("actor"),
        Document.filename.label("detail"),
      )
      .join(User, Document.user_id == User.user_id)
      .order_by(Document.upload_timestamp.desc())
      .limit(limit)
    )

    # Recent user-sent chat messages
    chats = (
      select(
        ChatHistory.timestamp.label("ts"),
        literal("chat").label("type"),
        User.email.label("actor"),
        func.left(ChatHistory.content, 80).label("detail"),
      )
      .join(User, ChatHistory.user_id == User.user_id)
      .where(ChatHistory.role == "user")
      .order_by(ChatHistory.timestamp.desc())
      .limit(limit)
    )

    # Recent LLM errors
    errors = (
      select(
        LLMLog.timestamp.label("ts"),
        literal("llm_error").label("type"),
        LLMLog.module.label("actor"),
        func.coalesce(
          func.left(LLMLog.error_message, 80),
          literal("Unknown error"),
        ).label("detail"),
      )
      .where(LLMLog.success == False)
      .order_by(LLMLog.timestamp.desc())
      .limit(limit)
    )

    combined = union_all(uploads, chats, errors).subquery()
    result = await db.execute(
      select(combined).order_by(combined.c.ts.desc()).limit(limit)
    )
    rows = result.all()
    return [
      {
        "timestamp": r.ts.isoformat() if r.ts else None,
        "type":      r.type,
        "actor":     r.actor,
        "detail":    r.detail,
      }
      for r in rows
    ]
