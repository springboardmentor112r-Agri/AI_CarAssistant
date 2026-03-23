"""
Documents API router.
Handles: upload, status polling, list, detail, delete, retry SLA.
"""
import logging

from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, BackgroundTasks
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core import database as _db
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, Document
from app.schemas.schemas import DocumentRead, DocumentDetail
from app.services.extraction_service import extraction_service
from app.services.document_service import (
    create_document,
    update_document_status,
    update_extracted_text,
    update_sla,
    get_document,
    get_document_with_text,
    list_user_documents,
    delete_document,
)

router = APIRouter()
logger = logging.getLogger("app.documents")

# ─── ALLOWED MIME TYPES ───────────────────────────────────────────────
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/plain",
    "text/csv",
    "text/html",
    "text/rtf",
    "message/rfc822",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/heic",
    "image/bmp",
    "image/webp",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# ─── BACKGROUND TASK: FULL PROCESSING PIPELINE ────────────────────────
async def process_document(
    doc_id: UUID,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
):
    """
    Background task: full pipeline for a newly uploaded document.

    Stage 1: Text extraction
      SUCCESS -> status = "extraction_complete", raw_text saved
      FAILURE -> status = "error", document DELETED (nothing to retry)

    Stage 2: SLA extraction (LLM)
      SUCCESS -> status = "ready"
      FAILURE -> status = "sla_failed" (user can retry)
    """
    async with _db.AsyncSessionLocal() as db:
        try:
            # Check document still exists (user may have closed/cancelled)
            doc_check = await db.execute(
                select(Document).where(Document.doc_id == doc_id)
            )
            if not doc_check.scalar_one_or_none():
                return  # Document was deleted, nothing to do

            await update_document_status(db, doc_id, "processing")

            # Stage 1: Extract text
            raw_text = await extraction_service.extract_text(
                file_bytes, filename, mime_type
            )

            # Check again before saving — user may have cancelled
            doc_check = await db.execute(
                select(Document).where(Document.doc_id == doc_id)
            )
            if not doc_check.scalar_one_or_none():
                return

            await update_extracted_text(db, doc_id, raw_text)
            # Status is now "extraction_complete"

            # Stage 2: SLA extraction
            # If this fails with SLAExtractionError, _run_sla_extraction
            # sets sla_failed internally — no extra handling needed here
            await _run_sla_extraction(db, doc_id, raw_text)

        except Exception as e:
            # Stage 1 failure (extraction never completed)
            # — keep doc with error status so frontend can show it
            try:
                doc_check = await db.execute(
                    select(Document).where(Document.doc_id == doc_id)
                )
                doc_row = doc_check.scalar_one_or_none()
                if doc_row:
                    if doc_row.processing_status in (
                        "pending", "processing"
                    ):
                        # Extraction never completed — keep doc
                        # so frontend sees the error and stops polling
                        err_str = str(e)[:200]
                        await update_document_status(
                            db, doc_id, "error",
                            f"Text extraction failed: {err_str}. "
                            f"Please re-upload in a different format "
                            f"(e.g. native PDF or DOCX)."
                        )
                        logger.exception(
                            "document extraction failed: doc_id=%s",
                            doc_id,
                        )
                    else:
                        # Extraction completed but something else
                        # failed — keep the document for SLA retry
                        await update_document_status(
                            db, doc_id, "sla_failed",
                            f"AI analysis failed: {str(e)[:200]}. "
                            f"Click 'Retry' to try again."
                        )
            except Exception:
                pass


# ─── SLA PROGRESS TRACKING ────────────────────────────────────────────
# In-memory dict: doc_id -> { step, total, message }
# Allows status endpoint to report live progress during SLA extraction.
import asyncio as _asyncio
_sla_progress: dict[str, dict] = {}


# ─── SLA EXTRACTION WORKFLOW (shared by upload + retry) ───────────────
async def _run_sla_extraction(
    db: AsyncSession,
    doc_id: UUID,
    raw_text: str,
):
    """
    Runs SLA extraction workflow.
    On transient LLM failures (rate limit, context window, network):
      -> sets status = 'sla_failed' with error reason
      -> increments sla_retry_count
      -> user can retry via POST /{doc_id}/retry-sla
    On success:
      -> sets status = 'ready' with sla_json + fairness score
    """
    from app.services.sla_service import sla_service, SLAExtractionError
    from app.services.document_service import increment_sla_retry

    doc_key = str(doc_id)

    # Check document still exists before SLA extraction
    doc_check = await db.execute(
        select(Document).where(Document.doc_id == doc_id)
    )
    if not doc_check.scalar_one_or_none():
        _sla_progress.pop(doc_key, None)
        return  # Document was deleted

    try:
        # Initial progress
        _sla_progress[doc_key] = {
            "step": 0, "total": 1, 
            "message": "Initializing analysis..."
        }

        # Progress callback for the service
        async def progress_callback(current, total, msg):
            _sla_progress[doc_key] = {
                "step": current,
                "total": total,
                "message": msg
            }
            logger.info(
                "sla progress: doc_id=%s step=%s/%s message=%s",
                doc_id,
                current,
                total,
                msg,
            )

        # Set the callback and run
        sla_service._progress_callback = progress_callback
        
        # Attempt SLA extraction — may raise SLAExtractionError
        # Wrap in overall 200-second timeout so it never hangs
        sla_result = await _asyncio.wait_for(
            sla_service.extract_sla(raw_text),
            timeout=200,
        )

        _sla_progress[doc_key] = {
            "step": 100, "total": 100,
            "message": "Computing fairness score..."
        }

        # Check document still exists after LLM calls
        doc_check = await db.execute(
            select(Document).where(Document.doc_id == doc_id)
        )
        if not doc_check.scalar_one_or_none():
            _sla_progress.pop(doc_key, None)
            return  # Document was deleted during analysis

        score = sla_service.compute_fairness_score(sla_result)
        vin = sla_result.get("vin")

        _sla_progress[doc_key] = {
            "step": 100, "total": 100,
            "message": "Saving results..."
        }
        await update_sla(db, doc_id, sla_result, score, vin)
        # Status is now "ready"

    except _asyncio.TimeoutError:
        logger.warning("sla timeout: doc_id=%s", doc_id)
        doc_check = await db.execute(
            select(Document).where(Document.doc_id == doc_id)
        )
        if not doc_check.scalar_one_or_none():
            _sla_progress.pop(doc_key, None)
            return
        await increment_sla_retry(db, doc_id)
        await update_document_status(
            db, doc_id, "sla_failed",
            "AI analysis timed out. Please retry.",
        )

    except SLAExtractionError as e:
        logger.warning(
            "sla extraction failed: doc_id=%s reason=%s detail=%s",
            doc_id,
            e.reason,
            e.detail,
        )
        # Check document still exists before updating
        doc_check = await db.execute(
            select(Document).where(Document.doc_id == doc_id)
        )
        if not doc_check.scalar_one_or_none():
            _sla_progress.pop(doc_key, None)
            return

        await increment_sla_retry(db, doc_id)
        await update_document_status(
            db, doc_id, "sla_failed", e.detail
        )

    except Exception as e:
        logger.exception("sla unexpected error: doc_id=%s", doc_id)
        try:
            await increment_sla_retry(db, doc_id)
            await update_document_status(
                db, doc_id, "sla_failed",
                f"Analysis failed unexpectedly. Please retry.",
            )
        except Exception:
            pass

    finally:
        _sla_progress.pop(doc_key, None)


# ─── POST /upload ──────────────────────────────────────────────────────
@router.post("/upload", response_model=DocumentRead)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a contract file.
    Creates document row, starts background processing.
    Returns immediately with doc_id for polling.
    """
    # Validate mime type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            400,
            f"File type '{file.content_type}' is not supported. "
            f"Please upload PDF, Word, Excel, image, or text files."
        )

    # Read file bytes
    file_bytes = await file.read()

    # Validate file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            400,
            f"File too large. Maximum allowed size is 50MB."
        )

    if len(file_bytes) == 0:
        raise HTTPException(400, "File is empty.")

    # Create document row
    doc = await create_document(
        db,
        user_id=current_user.user_id,
        filename=file.filename,
        file_size=len(file_bytes),
        mime_type=file.content_type,
    )

    # Start background processing
    background_tasks.add_task(
        process_document,
        doc.doc_id,
        file_bytes,
        file.filename,
        file.content_type,
    )

    return doc


# ─── GET /list ─────────────────────────────────────────────────────────
@router.get("/list", response_model=list[DocumentRead])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the current user."""
    return await list_user_documents(db, current_user.user_id)


# ─── GET /{doc_id} ─────────────────────────────────────────────────────
@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document_detail(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full document detail including sla_json and extracted text."""
    doc = await get_document(db, doc_id, current_user.user_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


# ─── GET /{doc_id}/status ──────────────────────────────────────────────
@router.get("/{doc_id}/status")
async def get_document_status(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Poll processing status.
    Frontend polls every 4 seconds until status is ready/error/sla_failed.
    Includes sla_progress if analysis is in progress.
    """
    doc = await get_document(db, doc_id, current_user.user_id)
    if not doc:
        # Return "deleted" instead of 404 so frontend stops polling
        return {
            "doc_id": str(doc_id),
            "processing_status": "deleted",
            "error_message": "Document was removed.",
            "sla_retry_count": 0,
            "contract_fairness_score": None,
            "filename": None,
            "sla_progress": None,
        }

    # Include live progress if available
    progress = _sla_progress.get(str(doc_id))

    return {
        "doc_id": str(doc.doc_id),
        "processing_status": doc.processing_status,
        "error_message": doc.error_message,
        "sla_retry_count": doc.sla_retry_count,
        "contract_fairness_score": doc.contract_fairness_score,
        "filename": doc.filename,
        "sla_progress": progress,
    }


# ─── DELETE /{doc_id} ──────────────────────────────────────────────────
@router.delete("/{doc_id}")
async def delete_user_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a document and all its chat history.
    Also deletes Qdrant vectors for this document.
    """
    deleted = await delete_document(db, doc_id, current_user.user_id)
    if not deleted:
        raise HTTPException(404, "Document not found")

    # Delete vectors from Qdrant
    try:
        import asyncio
        from app.services.vector_service import vector_service
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: vector_service.delete_vectors_for_document(
                str(doc_id)
            )
        )
    except Exception:
        pass  # Non-fatal: vectors will be orphaned but not harmful

    return {"message": "Deleted successfully"}


# ─── POST /{doc_id}/retry-sla ──────────────────────────────────────────
@router.post("/{doc_id}/retry-sla")
async def retry_sla_extraction(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retry SLA extraction SYNCHRONOUSLY (inline).
    Runs the full SLA extraction in this request — does NOT use
    background tasks (which get killed on server restart).
    Returns only after analysis completes or fails.
    """
    doc = await get_document_with_text(
        db, doc_id, current_user.user_id
    )

    if not doc:
        raise HTTPException(404, "Document not found")

    if doc.processing_status == "ready":
        raise HTTPException(
            400, "Document is already analysed successfully"
        )

    if doc.processing_status not in (
        "sla_failed", "extraction_complete"
    ):
        raise HTTPException(
            400,
            f"Document cannot be retried in "
            f"status: {doc.processing_status}"
        )

    if not doc.raw_extracted_text:
        from app.services.document_service import delete_document_by_id
        await delete_document_by_id(db, doc_id)
        raise HTTPException(
            400,
            "No extracted text found. "
            "Document has been removed — please upload again."
        )

    # Enforce max retry limit
    MAX_RETRIES = 5
    if doc.sla_retry_count >= MAX_RETRIES:
        from app.services.document_service import delete_document_by_id
        await delete_document_by_id(db, doc_id)
        raise HTTPException(
            400,
            f"Maximum retry attempts ({MAX_RETRIES}) exceeded. "
            f"Document has been removed — please upload again."
        )

    # Set status to extraction_complete for progress tracking
    await update_document_status(
        db, doc_id, "extraction_complete"
    )

    # Run SLA extraction INLINE — not as background task
    logger.info("sla inline retry started: doc_id=%s", doc_id)
    await _run_sla_extraction(db, doc_id, doc.raw_extracted_text)

    # Re-fetch the document to get updated status
    doc = await get_document(db, doc_id, current_user.user_id)
    status = doc.processing_status if doc else "deleted"

    return {
        "doc_id": str(doc_id),
        "processing_status": status,
        "message": (
            "Analysis complete!"
            if status == "ready"
            else "Analysis failed. You can retry."
        ),
        "sla_retry_count": doc.sla_retry_count if doc else 0,
    }
