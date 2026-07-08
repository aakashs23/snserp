"""Chat API – RAG-powered Q&A over uploaded documents.

Uses the provider-agnostic ai_service for all LLM and embedding
interactions.  All heavy calls run in threads to keep the async
event-loop free, preventing asyncpg/greenlet connection errors.

Phase 6: Advanced RAG — query expansion → retrieve 20 → cross-encoder
rerank → parent context → compress → generate.
"""

import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request as FastAPIRequest
import chromadb
from sqlalchemy import or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import settings
from app.schemas.chat import (
    ChatRequest, ChatResponse, Citation,
    ChatSessionResponse, ChatMessageResponse,
)
from app.models.users import User
from app.services.activity_service import log_activity
from app.models.documents import Document, DocumentAI, DocumentMetadata
from app.models.chat import AIChatSession, AIChatMessage
from app.middleware.auth import get_current_user
from app.database.session import get_db
from app.services.ai_service import ai_generate, ai_embed, extract_confidence
from app.services.chroma_utils import ensure_chroma_collection, is_embedding_dimension_mismatch
from app.services.rag_service import (
    expand_query,
    rerank_chunks,
    retrieve_parent_context,
    compress_context,
)

logger = logging.getLogger(__name__)

router = APIRouter()
_chat_limiter = Limiter(key_func=get_remote_address)

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
collection = ensure_chroma_collection(chroma_client, "snserp_documents")


# ─── Session endpoints ───────────────────────────────────────────────────────
@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIChatSession)
        .where(AIChatSession.user_id == current_user.id)
        .order_by(desc(AIChatSession.created_at))
        .limit(20)
    )
    return result.scalars().all()


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(AIChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(AIChatMessage)
        .where(AIChatMessage.session_id == session_id)
        .order_by(AIChatMessage.created_at)
    )
    return result.scalars().all()


# ─── Internal helpers ─────────────────────────────────────────────────────────
async def _rewrite_query(query: str, history: List[AIChatMessage]) -> str:
    """Use the LLM to rewrite the query using conversation history
    so it becomes a standalone question."""
    if not history:
        return query

    history_text = ""
    for msg in history[-6:]:  # last 6 messages for richer context
        history_text += f"{msg.role.capitalize()}: {msg.message}\n"

    prompt = (
        "Given the following conversation and a follow-up question, "
        "rephrase the follow-up question to be a standalone question. "
        "If the follow-up question is already standalone, return it exactly. "
        "Do NOT answer the question, just return the standalone question.\n\n"
        f"Chat History:\n{history_text}\n"
        f"Follow Up Input: {query}\n"
        "Standalone question:"
    )

    rewritten, _ = await ai_generate(prompt, temperature=0.0)
    return rewritten.strip()


async def _get_permitted_doc_ids(db: AsyncSession, current_user: User) -> list[str]:
    """Fetch document IDs the current user is allowed to access."""
    doc_query = select(Document.id).where(Document.is_deleted == False)  # noqa: E712
    if current_user.role and current_user.role.name in ["viewer", "accountant"]:
        from app.models.document_permissions import DocumentPermission
        doc_query = (
            doc_query
            .join(DocumentPermission, Document.id == DocumentPermission.document_id)
            .where(
                DocumentPermission.user_id == current_user.id,
                DocumentPermission.can_view == True,  # noqa: E712
                Document.status == "approved",
            )
        )
    result = await db.execute(doc_query)
    return [str(doc_id) for doc_id in result.scalars().all()]


async def _keyword_search(
    db: AsyncSession,
    permitted_doc_ids: list[str],
    query: str,
) -> tuple[list[str], list]:
    """Postgres keyword search over document metadata.
    Returns (matched_doc_ids, raw_matches)."""
    query_tokens = [t for t in query.split() if len(t) > 3]
    if not query_tokens:
        return [], []

    filters = []
    for term in query_tokens:
        pattern = f"%{term}%"
        filters.extend([
            Document.original_name.ilike(pattern),
            Document.ai_category.ilike(pattern),
            DocumentMetadata.title.ilike(pattern),
            DocumentMetadata.description.ilike(pattern),
            DocumentMetadata.invoice_number.ilike(pattern),
            DocumentMetadata.customer_details.ilike(pattern),
            DocumentMetadata.gst_number.ilike(pattern),
        ])

    db_result = await db.execute(
        select(Document.id, Document.original_name, DocumentAI.ocr_text)
        .outerjoin(DocumentMetadata, DocumentMetadata.document_id == Document.id)
        .outerjoin(DocumentAI, DocumentAI.document_id == Document.id)
        .where(
            Document.id.in_([uuid.UUID(id_str) for id_str in permitted_doc_ids]),
            or_(*filters),
        )
        .limit(15)
    )
    matches = db_result.all()
    return [str(m.id) for m in matches], matches


async def _chroma_search(
    query_embedding: list[float],
    doc_id_filter: list[str],
    n_results: int = 20,
) -> dict:
    """Search ChromaDB with dimension-mismatch safety."""
    try:
        return collection.query(
            query_embeddings=[query_embedding],
            where={"document_id": {"$in": doc_id_filter}},
            n_results=n_results,
            include=["documents", "metadatas"],
        )
    except Exception as exc:
        if is_embedding_dimension_mismatch(exc):
            logger.warning("Chroma search skipped due to embedding mismatch: %s", exc)
            return {"documents": [[]], "metadatas": [[]]}
        raise


async def _multi_query_retrieve(
    queries: list[str],
    permitted_doc_ids: list[str],
    n_results_per_query: int = 20,
) -> tuple[list[str], list[dict]]:
    """Embed multiple query variants and merge ChromaDB results."""
    all_docs: list[str] = []
    all_metas: list[dict] = []
    seen: set[str] = set()

    for q in queries:
        embedding = await ai_embed(q)
        results = await _chroma_search(embedding, permitted_doc_ids, n_results_per_query)

        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                # Use first 100 chars as dedup key
                key = doc[:100]
                if key not in seen:
                    seen.add(key)
                    all_docs.append(doc)
                    all_metas.append(results["metadatas"][0][i] if results["metadatas"] else {})

    return all_docs, all_metas


async def _hybrid_search(
    db: AsyncSession,
    current_user: User,
    standalone_query: str,
) -> tuple[list[str], list[dict]]:
    """Full hybrid retrieval pipeline:
    1. Permission filter
    2. Query expansion (multi-query)
    3. ChromaDB semantic search (Top-20 per variant)
    4. Postgres keyword search boost
    5. OCR fallback
    """
    permitted_doc_ids = await _get_permitted_doc_ids(db, current_user)
    if not permitted_doc_ids:
        return [], []

    # Query expansion
    queries = await expand_query(standalone_query)
    logger.info(f"Expanded queries: {queries}")

    # Multi-query ChromaDB retrieval
    all_docs, all_metas = await _multi_query_retrieve(queries, permitted_doc_ids)

    # Keyword search boost
    db_matched_ids, db_matches = await _keyword_search(db, permitted_doc_ids, standalone_query)

    if db_matched_ids:
        try:
            q_embed = await ai_embed(standalone_query)
            boost = await _chroma_search(q_embed, db_matched_ids, 10)
            if boost["documents"] and boost["documents"][0]:
                seen = {d[:100] for d in all_docs}
                for i, doc in enumerate(boost["documents"][0]):
                    key = doc[:100]
                    if key not in seen:
                        seen.add(key)
                        all_docs.append(doc)
                        all_metas.append(boost["metadatas"][0][i] if boost["metadatas"] else {})
        except Exception as e:
            if is_embedding_dimension_mismatch(e):
                logger.warning("Chroma boost skipped due to embedding mismatch: %s", e)
            else:
                logger.warning(f"Chroma keyword-boost failed: {e}")

    # OCR text fallback if nothing from vectors
    if not all_docs and db_matches:
        for match in db_matches:
            if match.ocr_text:
                all_docs.append(match.ocr_text[:4000])
                all_metas.append({
                    "file_name": match.original_name,
                    "document_id": str(match.id),
                    "page_number": 1,
                    "chunk_index": 0,
                })

    return all_docs, all_metas


# ─── Main query endpoint ──────────────────────────────────────────────────────
@router.post("/query", response_model=ChatResponse)
@_chat_limiter.limit(settings.rate_limit_ai)
async def chat_query(
    http_request: FastAPIRequest,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        # ── Session management ──
        session_id = request.session_id
        history: list[AIChatMessage] = []
        if not session_id:
            new_session = AIChatSession(
                id=uuid.uuid4(),
                user_id=current_user.id,
                title=request.message[:50],
            )
            db.add(new_session)
            session_id = str(new_session.id)
            await db.flush()
        else:
            try:
                session_uuid = uuid.UUID(session_id)
                hist_res = await db.execute(
                    select(AIChatMessage)
                    .where(AIChatMessage.session_id == session_uuid)
                    .order_by(AIChatMessage.created_at)
                )
                history = list(hist_res.scalars().all())
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid session_id")

        # ── Rewrite query using conversation context ──
        standalone_query = await _rewrite_query(request.message, history)
        logger.info(f"Original: {request.message} -> Standalone: {standalone_query}")

        # ── Persist user message ──
        user_msg = AIChatMessage(
            id=uuid.uuid4(),
            session_id=uuid.UUID(session_id),
            role="user",
            message=request.message,
        )
        db.add(user_msg)
        await db.flush()

        # ── Phase 6: Advanced retrieval pipeline ──
        all_docs, all_metas = await _hybrid_search(db, current_user, standalone_query)

        # Cross-encoder reranking: Top-20 → Top-5
        if all_docs:
            ranked = await rerank_chunks(
                standalone_query, all_docs, all_metas, top_k=5
            )
        else:
            ranked = []

        # Parent context retrieval: expand with ±1 neighbors
        if ranked:
            ranked = retrieve_parent_context(ranked, all_docs, all_metas)

        # Context compression: deduplicate & merge contiguous
        if ranked:
            ranked = compress_context(ranked)

        # ── Build citations ──
        citations: list[Citation] = []
        context_chunks: list[str] = []

        for text, meta, score in ranked:
            file_name = meta.get("file_name", "Unknown")
            page_num = meta.get("page_number")
            chunk_idx = meta.get("chunk_index")

            page_label = f" (Page {page_num})" if page_num else ""
            context_chunks.append(
                f"[Source: {file_name}{page_label}]\n{text}"
            )
            citations.append(
                Citation(
                    document_id=meta.get("document_id", ""),
                    file_name=file_name,
                    snippet=text[:200] + "..." if len(text) > 200 else text,
                    page_number=page_num if isinstance(page_num, int) else None,
                    chunk_index=chunk_idx if isinstance(chunk_idx, int) else None,
                    relevance_score=round(float(score), 4),
                )
            )

        context = "\n\n---\n\n".join(context_chunks)

        # ── Build prompt ──
        if context:
            prompt = (
                "You are the Sri Naga Sai ERP AI Assistant. "
                "Your goal is to answer the user's question naturally, conversationally, and accurately based strictly on the provided document context. "
                "If the answer cannot be found in the context, politely say "
                "\"I could not find the answer to this in the uploaded documents.\"\n"
                "Do NOT hallucinate unsupported facts or use outside knowledge.\n"
                "When answering:\n"
                "- Explain your reasoning clearly.\n"
                "- Use complete sentences.\n"
                "- Summarize broad topics where appropriate.\n"
                "- Use markdown tables when comparing data or if it is helpful.\n"
                "- Use bullet points for lists or step-by-step instructions.\n"
                "When multiple documents are relevant, synthesize information across them "
                "and cite which documents and page numbers support each point.\n\n"
                "Structure your response logically. At the very end of your answer, on a new line, add a confidence tag "
                "like [CONFIDENCE: 0.85] indicating how confident you are (0.0–1.0).\n\n"
                f"Context:\n{context}\n\n"
                f"User Question: {standalone_query}"
            )
        else:
            prompt = (
                "You are the Sri Naga Sai ERP AI Assistant. "
                "The user asked a question, but no relevant company documents "
                "were found in the system to answer it. "
                "Politely inform the user that you don't have any uploaded "
                "documents matching their query, but you can help if they "
                "upload relevant files.\n\n"
                f"User Question: {standalone_query}"
            )

        # ── Generate answer (with failover) ──
        raw_answer, provider_name = await ai_generate(prompt)
        answer, confidence = extract_confidence(raw_answer)

        # ── Persist AI response ──
        ai_msg = AIChatMessage(
            id=uuid.uuid4(),
            session_id=uuid.UUID(session_id),
            role="ai",
            message=answer,
        )
        db.add(ai_msg)
        await db.flush()

        return ChatResponse(
            session_id=session_id,
            answer=answer,
            citations=citations,
            confidence=confidence,
            provider=provider_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat API error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the chat query: {str(e)}",
        )
