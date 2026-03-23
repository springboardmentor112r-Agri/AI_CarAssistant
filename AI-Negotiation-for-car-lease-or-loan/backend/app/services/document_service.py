"""
Document CRUD operations for Neon PostgreSQL.
All functions are async, use AsyncSession.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.models import Document


async def create_document(
    db: AsyncSession,
    user_id: UUID,
    filename: str,
    file_size: int,
    mime_type: str,
) -> Document:
    """
    Create document row with status 'pending'.
    Returns created Document.
    """
    doc = Document(
        user_id=user_id,
        filename=filename,
        processing_status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def update_document_status(
    db: AsyncSession,
    doc_id: UUID,
    status: str,
    error_message: str | None = None,
):
    """
    Update processing_status and optionally error_message.
    """
    values = {"processing_status": status}
    if error_message is not None:
        values["error_message"] = error_message
    await db.execute(
        update(Document)
        .where(Document.doc_id == doc_id)
        .values(**values)
    )
    await db.commit()


async def update_extracted_text(
    db: AsyncSession,
    doc_id: UUID,
    raw_text: str,
):
    """
    Save extracted text and set status to 'extraction_complete'.
    Called after text extraction succeeds.
    """
    await db.execute(
        update(Document)
        .where(Document.doc_id == doc_id)
        .values(
            raw_extracted_text=raw_text,
            processing_status="extraction_complete",
        )
    )
    await db.commit()


async def update_sla(
    db: AsyncSession,
    doc_id: UUID,
    sla_json: dict,
    fairness_score: float,
    vin: str | None,
):
    """
    Save SLA extraction results and set status to 'ready'.
    Called after successful LLM analysis.
    """
    values = {
        "sla_json": sla_json,
        "contract_fairness_score": fairness_score,
        "processing_status": "ready",
    }
    if vin:
        values["vin"] = vin
    await db.execute(
        update(Document)
        .where(Document.doc_id == doc_id)
        .values(**values)
    )
    await db.commit()


async def increment_sla_retry(
    db: AsyncSession,
    doc_id: UUID,
) -> int:
    """
    Increment sla_retry_count by 1.
    Returns the new count.
    """
    await db.execute(
        update(Document)
        .where(Document.doc_id == doc_id)
        .values(sla_retry_count=Document.sla_retry_count + 1)
    )
    await db.commit()
    result = await db.execute(
        select(Document.sla_retry_count)
        .where(Document.doc_id == doc_id)
    )
    return result.scalar_one()


async def delete_document_by_id(
    db: AsyncSession,
    doc_id: UUID,
):
    """
    Hard delete document by doc_id only (no user_id check).
    Used internally when total SLA failure occurs.
    CASCADE removes chat_history automatically.
    """
    await db.execute(
        delete(Document).where(Document.doc_id == doc_id)
    )
    await db.commit()


async def get_document(
    db: AsyncSession,
    doc_id: UUID,
    user_id: UUID,
) -> Document | None:
    """
    Fetch document by doc_id + user_id (ownership check).
    Returns None if not found or not owned by user.
    """
    result = await db.execute(
        select(Document).where(
            Document.doc_id == doc_id,
            Document.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_document_with_text(
    db: AsyncSession,
    doc_id: UUID,
    user_id: UUID,
) -> Document | None:
    """
    Same as get_document but name makes intent clear.
    Used by retry endpoint — needs raw_extracted_text.
    """
    return await get_document(db, doc_id, user_id)


async def get_document_for_chat(
    db: AsyncSession,
    doc_id: UUID,
    user_id: UUID,
) -> Document | None:
    """
    Fetch ready document for chat.
    Returns None if not found, not owned, or not ready.
    """
    result = await db.execute(
        select(Document).where(
            Document.doc_id == doc_id,
            Document.user_id == user_id,
            Document.processing_status == "ready",
        )
    )
    return result.scalar_one_or_none()


async def list_user_documents(
    db: AsyncSession,
    user_id: UUID,
) -> list[Document]:
    """
    List all documents for a user, newest first.
    """
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.upload_timestamp.desc())
    )
    return result.scalars().all()


async def delete_document(
    db: AsyncSession,
    doc_id: UUID,
    user_id: UUID,
) -> bool:
    """
    Delete document by doc_id + user_id (ownership check).
    Returns True if deleted, False if not found.
    """
    result = await db.execute(
        delete(Document).where(
            Document.doc_id == doc_id,
            Document.user_id == user_id,
        )
    )
    await db.commit()
    return result.rowcount > 0
