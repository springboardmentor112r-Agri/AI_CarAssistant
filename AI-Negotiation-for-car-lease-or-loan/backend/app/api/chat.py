from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, desc
from uuid import uuid4, UUID
import json

from app.core import database
from app.api.deps import get_current_user
from app.models.models import User, ChatHistory
from app.schemas.schemas import ChatMessageCreate, ChatMessageRead, NewThreadRequest
from app.services.chat_service import chat_service
from app.services.document_service import get_document

router = APIRouter()

@router.post("/message")
async def chat_message(
    body: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
):
    """
    SSE endpoint for chat streaming.
    Session opened and closed inside generator
    to prevent connection leaks.
    """
    async def event_generator():
        async with database.AsyncSessionLocal() as db:
            try:
                async for token in chat_service.stream_message(
                    db=db,
                    user_id=current_user.user_id,
                    doc_id=body.doc_id,
                    thread_id=body.thread_id,
                    user_message=body.message,
                ):
                    # Escape newlines in token so SSE frame stays intact
                    safe_token = token.replace('\n', '\\n')
                    yield f"data: {safe_token}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                await db.rollback()
                error_str = str(e).lower()
                if "rate limit" in error_str or "429" in error_str:
                    yield "data: [ERROR]rate limit\n\n"
                elif "not found" in error_str:
                    yield "data: [ERROR]document not found\n\n"
                else:
                    yield "data: [ERROR]stream failed\n\n"
            finally:
                # Explicit close — guaranteed even on disconnect
                await db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        }
    )

@router.post("/new-thread")
async def create_new_thread(
    body: NewThreadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Initialize a new chat thread for a document.
    """
    doc = await get_document(db, body.doc_id, current_user.user_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.processing_status != "ready":
        raise HTTPException(400, "Document not ready for chat")

    thread_id = uuid4()
    return {
        "thread_id": str(thread_id),
        "doc_id": str(body.doc_id),
        "message": "Thread created. Start chatting."
    }

@router.get("/history/{thread_id}", response_model=list[ChatMessageRead])
async def get_thread_history(
    thread_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Fetch message history for a specific thread.
    """
    # Verify thread belongs to current user
    # Check the first message in the thread
    first_msg_check = await db.execute(
        select(ChatHistory.user_id)
        .where(ChatHistory.thread_id == thread_id)
        .limit(1)
    )
    first_msg_user_id = first_msg_check.scalar_one_or_none()
    
    if first_msg_user_id and first_msg_user_id != current_user.user_id:
        raise HTTPException(403, "Not authorized to view this thread")

    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.thread_id == thread_id)
        .order_by(ChatHistory.timestamp.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()

@router.get("/threads/{doc_id}")
async def list_document_threads(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    List all chat threads for a specific document.
    """
    # Validate document ownership
    doc = await get_document(db, doc_id, current_user.user_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    # Get thread summaries
    # We want thread_id, started, last_updated, message_count
    result = await db.execute(
        select(
            ChatHistory.thread_id,
            func.min(ChatHistory.timestamp).label("started"),
            func.max(ChatHistory.timestamp).label("last_updated"),
            func.count(ChatHistory.message_id).label("message_count")
        )
        .where(ChatHistory.doc_id == doc_id, ChatHistory.user_id == current_user.user_id)
        .group_by(ChatHistory.thread_id)
        .order_by(desc("last_updated"))
    )
    
    threads = []
    for row in result.all():
        # Fetch first user message for preview
        preview_result = await db.execute(
            select(ChatHistory.content)
            .where(
                ChatHistory.thread_id == row.thread_id,
                ChatHistory.role == "user"
            )
            .order_by(ChatHistory.timestamp.asc())
            .limit(1)
        )
        preview = preview_result.scalar_one_or_none() or ""
        if len(preview) > 60:
            preview = preview[:57] + "..."

        threads.append({
            "thread_id": str(row.thread_id),
            "started": row.started,
            "last_updated": row.last_updated,
            "message_count": row.message_count,
            "preview": preview,
        })
    
    return threads

@router.delete("/thread/{thread_id}")
async def delete_chat_thread(
    thread_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Delete a chat thread and its history.
    """
    # Verify thread belongs to current user
    check_result = await db.execute(
        select(ChatHistory.user_id)
        .where(ChatHistory.thread_id == thread_id)
        .limit(1)
    )
    user_id = check_result.scalar_one_or_none()
    
    if not user_id:
        raise HTTPException(404, "Thread not found")
    if user_id != current_user.user_id:
        raise HTTPException(403, "Not authorized to delete this thread")

    from sqlalchemy import delete
    await db.execute(
        delete(ChatHistory)
        .where(ChatHistory.thread_id == thread_id, ChatHistory.user_id == current_user.user_id)
    )
    await db.commit()

    return {"message": "Thread deleted"}
