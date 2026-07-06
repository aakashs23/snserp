"""Chat API – RAG-powered Q&A over uploaded documents.

Uses the provider-agnostic ai_service for all LLM and embedding
interactions.  All heavy calls run in threads to keep the async
event-loop free, preventing asyncpg/greenlet connection errors.
"""

import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
import chromadb
from sqlalchemy import or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

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

logger = logging.getLogger(__name__)

router = APIRouter()

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


async def _hybrid_search(db: AsyncSession, current_user: User, query: str):
    """Combine ChromaDB semantic search with Postgres metadata search,
    filtered by the current user's document permissions."""

    # 0. Get allowed document IDs
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

    permitted_docs_res = await db.execute(doc_query)
    permitted_doc_ids = [str(doc_id) for doc_id in permitted_docs_res.scalars().all()]

    if not permitted_doc_ids:
        return {"documents": [], "metadatas": []}

    # 1. Postgres keyword search
    query_tokens = [t for t in query.split() if len(t) > 3]
    db_matched_ids: list[str] = []
    db_matches = []

    if query_tokens:
        filters = []
        for term in query_tokens:
            pattern = f"%{term}%"
            filters.extend([
                Document.original_name.ilike(pattern),
                Document.ai_category.ilike(pattern),
                DocumentMetadata.title.ilike(pattern),
                DocumentMetadata.description.ilike(pattern),
            ])

        db_result = await db.execute(
            select(Document.id, Document.original_name, DocumentAI.ocr_text)
            .outerjoin(DocumentMetadata, DocumentMetadata.document_id == Document.id)
            .outerjoin(DocumentAI, DocumentAI.document_id == Document.id)
            .where(
                Document.id.in_([uuid.UUID(id_str) for id_str in permitted_doc_ids]),
                or_(*filters),
            )
            .limit(10)
        )
        db_matches = db_result.all()
        db_matched_ids = [str(m.id) for m in db_matches]

    # 2. Embed the query (non-blocking via ai_service)
    query_embedding = await ai_embed(query)

    # 3. ChromaDB semantic search
    chroma_results = {"documents": [[]], "metadatas": [[]]}
    try:
        chroma_results = collection.query(
            query_embeddings=[query_embedding],
            where={"document_id": {"$in": permitted_doc_ids}},
            n_results=10,
            include=["documents", "metadatas"],
        )
    except Exception as exc:
        if is_embedding_dimension_mismatch(exc):
            logger.warning(
                "Skipping Chroma semantic search due to legacy embedding mismatch. "
                "Existing vectors need to be reindexed with the current embedding model: %s",
                exc,
            )
        else:
            raise

    # Boost: pull additional chunks from DB-matched documents
    if db_matched_ids and chroma_results.get("documents") is not None:
        try:
            db_chroma_results = collection.query(
                query_embeddings=[query_embedding],
                where={"document_id": {"$in": db_matched_ids}},
                n_results=5,
                include=["documents", "metadatas"],
            )
            if (
                db_chroma_results["documents"]
                and len(db_chroma_results["documents"][0]) > 0
            ):
                if not chroma_results["documents"] or not chroma_results["documents"][0]:
                    chroma_results = db_chroma_results
                else:
                    existing = set(chroma_results["documents"][0])
                    for i, doc in enumerate(db_chroma_results["documents"][0]):
                        if doc not in existing:
                            chroma_results["documents"][0].append(doc)
                            chroma_results["metadatas"][0].append(
                                db_chroma_results["metadatas"][0][i]
                            )
        except Exception as e:
            if is_embedding_dimension_mismatch(e):
                logger.warning(
                    "Skipping Chroma boost search due to embedding mismatch: %s",
                    e,
                )
            else:
                logger.warning(f"Chroma filtered search failed: {e}")

    # 4. Fallback: inject raw OCR text from Postgres if vector search empty
    if (
        not chroma_results.get("documents") or not chroma_results["documents"][0]
    ) and db_matches:
        docs = []
        metas = []
        for match in db_matches:
            if match.ocr_text:
                docs.append(match.ocr_text[:4000])
                metas.append(
                    {"file_name": match.original_name, "document_id": str(match.id)}
                )
        chroma_results["documents"] = [docs]
        chroma_results["metadatas"] = [metas]

    return chroma_results


# ─── Main query endpoint ──────────────────────────────────────────────────────
@router.post("/query", response_model=ChatResponse)
async def chat_query(
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

        # ── Retrieve context ──
        results = await _hybrid_search(db, current_user, standalone_query)

        citations: list[Citation] = []
        context_chunks: list[str] = []

        if results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                context_chunks.append(
                    f"[Source: {meta.get('file_name', 'Unknown')}]\n{doc}"
                )
                citations.append(
                    Citation(
                        document_id=meta.get("document_id", ""),
                        file_name=meta.get("file_name", "Unknown"),
                        snippet=doc[:200] + "..." if len(doc) > 200 else doc,
                    )
                )

        context = "\n\n---\n\n".join(context_chunks)

        # ── Build prompt ──
        if context:
            prompt = (
                "You are the Sri Naga Sai ERP AI Assistant. "
                "Answer the user's question based strictly on the provided document context. "
                "If the answer cannot be found in the context, say "
                "\"I could not find the answer to this in the uploaded documents.\"\n"
                "Do NOT use outside knowledge.\n"
                "When multiple documents are relevant, synthesize information across them "
                "and cite which documents support each point.\n"
                "Be thorough yet concise.\n"
                "At the very end of your answer, on a new line, add a confidence tag "
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
