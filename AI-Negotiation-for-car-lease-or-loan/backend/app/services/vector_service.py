"""
Thread-scoped vector store service.
Handles chunking, embedding, storing, retrieving
and deleting contract text chunks in Qdrant Cloud.

KEY DESIGN DECISIONS:
  - Vectors stored per thread_id (not per doc_id)
  - Retrieval filtered by thread_id ONLY
  - Zero cross-document contamination guaranteed
  - Vectors created ONLY when user starts new chat
  - Vectors deleted when document is deleted
  - Embedding model runs locally on CPU (no API key)
"""

import uuid
import asyncio
import logging
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    PointStruct, Filter,
    FieldCondition, MatchValue,
)
from fastembed import TextEmbedding
from app.core.config import settings

COLLECTION_NAME = "car_contract_chunks"
VECTOR_DIM = 384          # all-MiniLM-L6-v2 output dimension
CHUNK_SIZE = 500          # chars per chunk
CHUNK_OVERLAP = 50        # overlap between chunks
TOP_K = 5                 # number of chunks to retrieve

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        # Lazily initialized to avoid network call at import time
        self.client = None
        # Lazily initialized to avoid blocking app startup on model download.
        self.encoder = None
        self._embedded_threads: set = set()
        self._collection_ready = False

    def _get_client(self):
        """
        Lazy-initialize Qdrant client on first use.
        Avoids blocking Render startup with remote connection validation.
        """
        if self.client is None:
            logger.info("[VectorService] Connecting to Qdrant")
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
            logger.info("[VectorService] Connected to Qdrant")
        return self.client

    def _get_encoder(self):
        """
        Lazy-load the embedding model on first use.
        This prevents Render startup timeout caused by model fetch at import time.
        """
        if self.encoder is None:
            logger.info("[VectorService] Loading embedding model")
            self.encoder = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("[VectorService] Embedding model ready")
        return self.encoder

    def _ensure_collection(self):
        """
        Create Qdrant collection if it does not exist.
        Called once on service initialization.
        Safe to call multiple times — checks before creating.
        """
        if self._collection_ready:
            return

        existing = [
            c.name
            for c in self._get_client().get_collections().collections
        ]
        if COLLECTION_NAME not in existing:
            logger.info("[VectorService] Creating Qdrant collection '%s'", COLLECTION_NAME)
            self._get_client().create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_DIM,
                    distance=Distance.COSINE,
                ),
            )
            # Create payload indexes for efficient filtering
            self._get_client().create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="thread_id",
                field_schema="keyword",
            )
            self._get_client().create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="doc_id",
                field_schema="keyword",
            )
            logger.info("[VectorService] Qdrant collection '%s' created", COLLECTION_NAME)
        self._collection_ready = True

    # ─── CHECK ───────────────────────────────────────────────
    def vectors_exist_for_thread(self, thread_id: str) -> bool:
        self._ensure_collection()

        # In-memory cache hit — instant (0ms)
        if thread_id in self._embedded_threads:
            return True
        # Cache miss — check Qdrant (network call ~300ms)
        result = self._get_client().scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="thread_id",
                        match=MatchValue(value=thread_id)
                    )
                ]
            ),
            limit=1,
        )
        exists = len(result[0]) > 0
        # Populate cache if found in Qdrant
        # Handles backend restart gracefully
        if exists:
            self._embedded_threads.add(thread_id)
        return exists

    # ─── CHUNK ───────────────────────────────────────────────
    def chunk_text(self, text: str) -> list[str]:
        """
        Split contract text into overlapping chunks.
        CHUNK_SIZE = 500 chars
        CHUNK_OVERLAP = 50 chars
        """
        if not text:
            return []
        chunks = []
        for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
            chunks.append(text[i:i + CHUNK_SIZE])
        return chunks

    async def ensure_vectors(
        self,
        document,
        user_id: str,
        doc_id: str,
        thread_id: str,
    ) -> None:
        """
        Async wrapper for embed_and_store.
        Ensures vectors exist for the thread.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.embed_and_store,
            document.raw_extracted_text or "",
            user_id,
            doc_id,
            thread_id,
            document.filename or "contract"
        )

    # ─── EMBED AND STORE ─────────────────────────────────────
    def embed_and_store(
        self,
        text: str,
        user_id: str,
        doc_id: str,
        thread_id: str,
        filename: str,
    ):
        """
        Chunk -> Embed -> Store in Qdrant.
        Called ONLY when user clicks New Chat for first time.
        Each chunk stored with thread_id for strict retrieval.

        Steps:
          1. Check if vectors already exist for thread_id
             YES -> skip (old thread revisit, no re-embedding)
             NO  -> proceed
          2. Split text into chunks
          3. Embed all chunks at once (batch for speed)
          4. Store in Qdrant with metadata
        """
        # Skip if already embedded for this thread
        if self.vectors_exist_for_thread(thread_id):
            logger.info("[VectorService] Reusing existing vectors for thread_id=%s", thread_id)
            return

        # Chunk the contract text
        chunks = self.chunk_text(text)
        if not chunks:
            logger.warning("[VectorService] No chunks produced for doc_id=%s thread_id=%s", doc_id, thread_id)
            return

        # Embed all chunks in one batch call (faster than one by one)
        encoder = self._get_encoder()
        embeddings = list(encoder.embed(chunks))

        # Build Qdrant points
        points = []
        for i, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload={
                        "user_id":     user_id,
                        "doc_id":      doc_id,
                        "thread_id":   thread_id,
                        "chunk_index": i,
                        "filename":    filename,
                        "text":        chunk,
                    }
                )
            )

        # Store in Qdrant (batch upsert)
        self._get_client().upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )
        logger.info(
            "[VectorService] Stored %d chunks for doc_id=%s thread_id=%s",
            len(points),
            doc_id,
            thread_id,
        )
        self._embedded_threads.add(thread_id)

    # ─── RETRIEVE ────────────────────────────────────────────
    def retrieve_relevant_chunks(
        self,
        query: str,
        thread_id: str,
        top_k: int = TOP_K,
    ) -> list[str]:
        """
        Retrieve most relevant chunks for user query.
        STRICT filter: thread_id ONLY.
        Zero cross-document contamination.

        Returns:
          List of chunk text strings (empty if nothing found)
        """
        try:
            # Collection ensures exists on first call
            self._ensure_collection()

            # Embed the user query
            encoder = self._get_encoder()
            query_vector = list(encoder.embed([query]))[0].tolist()

            # Search Qdrant with thread_id filter
            results = self._get_client().search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="thread_id",
                            match=MatchValue(value=thread_id),
                        )
                    ]
                ),
                limit=top_k,
            )

            if not results:
                return []

            # Return chunk texts sorted by chunk_index
            # (maintain document order for better context)
            sorted_results = sorted(
                results,
                key=lambda x: x.payload.get("chunk_index", 0)
            )
            return [r.payload["text"] for r in sorted_results]
        except Exception:
            logger.exception("[VectorService] Retrieval failed")
            return []

    def retrieve(self, query: str, thread_id: str, top_k: int = 5) -> list[str]:
        """Alias for retrieve_relevant_chunks for cleaner chat_service code."""
        return self.retrieve_relevant_chunks(query, thread_id, top_k)

    # ─── DELETE ──────────────────────────────────────────────
    def delete_vectors_for_document(self, doc_id: str):
        """
        Delete ALL vectors for a document.
        Called when document is deleted from PostgreSQL.
        Removes vectors from ALL threads of that document.
        Keeps Qdrant free tier storage clean.
        """
        self._get_client().delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            ),
        )

# Singleton instance
vector_service = VectorService()
