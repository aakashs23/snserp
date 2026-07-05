import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
import chromadb
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from sqlalchemy import or_, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.schemas.chat import ChatRequest, ChatResponse, Citation, ChatSessionResponse, ChatMessageResponse
from app.models.users import User
from app.services.activity_service import log_activity
from app.models.documents import Document, DocumentAI, DocumentMetadata
from app.models.chat import AIChatSession, AIChatMessage
from app.middleware.auth import get_current_user
from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
collection = chroma_client.get_or_create_collection(name="snserp_documents")

# Initialize Ollama LLM and Embeddings
llm = OllamaLLM(
    base_url=settings.ollama_base_url,
    model=settings.llm_model,
    temperature=0.2
)

embeddings = OllamaEmbeddings(
    base_url=settings.ollama_base_url,
    model=settings.embedding_model
)

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    session = await db.get(AIChatSession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
        
    result = await db.execute(
        select(AIChatMessage)
        .where(AIChatMessage.session_id == session_id)
        .order_by(AIChatMessage.created_at)
    )
    return result.scalars().all()

async def _rewrite_query(query: str, history: List[AIChatMessage]) -> str:
    """Use the LLM to rewrite the query using conversation history to make it standalone."""
    if not history:
        return query
        
    history_text = ""
    for msg in history[-4:]: # Use last 4 messages for context
        history_text += f"{msg.role.capitalize()}: {msg.message}\n"
        
    prompt = f"""
Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question. 
If the follow up question is already standalone, just return it exactly as is.
Do not answer the question, just return the standalone question.

Chat History:
{history_text}
Follow Up Input: {query}
Standalone question:"""
    
    rewritten = llm.invoke(prompt).strip()
    return rewritten

async def _hybrid_search(db: AsyncSession, current_user: User, query: str):
    """Combine ChromaDB semantic search with Postgres Metadata search, filtered by permissions."""
    # 0. Get allowed document IDs
    doc_query = select(Document.id).where(Document.is_deleted == False)
    if current_user.role.name in ["viewer", "accountant"]:
        from app.models.document_permissions import DocumentPermission
        doc_query = doc_query.join(DocumentPermission, Document.id == DocumentPermission.document_id).where(
            DocumentPermission.user_id == current_user.id,
            DocumentPermission.can_view == True,
            Document.status == "approved"
        )
    
    permitted_docs_res = await db.execute(doc_query)
    permitted_doc_ids = [str(doc_id) for doc_id in permitted_docs_res.scalars().all()]
    
    if not permitted_doc_ids:
        return {"documents": [], "metadatas": []}

    # 1. Postgres search based on query tokens
    query_tokens = [t for t in query.split() if len(t) > 3]
    db_matched_ids = []
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
                or_(*filters)
            )
            .limit(10)
        )
        db_matches = db_result.all()
        db_matched_ids = [str(m.id) for m in db_matches]

    # 2. Embed the query
    query_embedding = embeddings.embed_query(query)
    
    # 3. ChromaDB Search (broad semantic search + db matched specific search)
    # We'll pull top 10 chunks overall
    chroma_results = collection.query(
        query_embeddings=[query_embedding],
        where={"document_id": {"$in": permitted_doc_ids}},
        n_results=10,
        include=["documents", "metadatas"],
    )
    
    # Optional: If DB found specific documents, explicitly query Chroma for chunks from those documents
    if db_matched_ids:
        try:
            db_chroma_results = collection.query(
                query_embeddings=[query_embedding],
                where={"document_id": {"$in": db_matched_ids}},
                n_results=5,
                include=["documents", "metadatas"]
            )
            # Merge results
            if db_chroma_results['documents'] and len(db_chroma_results['documents'][0]) > 0:
                if not chroma_results['documents'] or not chroma_results['documents'][0]:
                    chroma_results = db_chroma_results
                else:
                    # Append unique chunks
                    existing_docs = set(chroma_results['documents'][0])
                    for i, doc in enumerate(db_chroma_results['documents'][0]):
                        if doc not in existing_docs:
                            chroma_results['documents'][0].append(doc)
                            chroma_results['metadatas'][0].append(db_chroma_results['metadatas'][0][i])
        except Exception as e:
            logger.warning(f"Chroma filtered search failed: {e}")

    # 4. Fallback: If vector search found absolutely nothing, inject raw OCR text from Postgres
    if (not chroma_results.get('documents') or not chroma_results['documents'][0]) and db_matches:
        docs = []
        metas = []
        for match in db_matches:
            if match.ocr_text:
                docs.append(match.ocr_text[:4000])  # limit to avoid context limits
                metas.append({"file_name": match.original_name, "document_id": str(match.id)})
        
        chroma_results['documents'] = [docs]
        chroma_results['metadatas'] = [metas]

    return chroma_results

@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Session Management
        session_id = request.session_id
        history = []
        if not session_id:
            # Create new session
            new_session = AIChatSession(
                id=uuid.uuid4(),
                user_id=current_user.id,
                title=request.message[:50]
            )
            db.add(new_session)
            session_id = str(new_session.id)
            await db.commit()
        else:
            # Fetch history
            try:
                session_uuid = uuid.UUID(session_id)
                hist_res = await db.execute(
                    select(AIChatMessage)
                    .where(AIChatMessage.session_id == session_uuid)
                    .order_by(AIChatMessage.created_at)
                )
                history = hist_res.scalars().all()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid session_id")

        # Rewrite query if there is history
        standalone_query = await _rewrite_query(request.message, history)
        logger.info(f"Original: {request.message} -> Standalone: {standalone_query}")

        # Save user message
        user_msg = AIChatMessage(
            id=uuid.uuid4(),
            session_id=uuid.UUID(session_id),
            role="user",
            message=request.message
        )
        db.add(user_msg)

        # Retrieve Context
        results = await _hybrid_search(db, current_user, standalone_query)
        
        citations = []
        context_chunks = []
        
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i] if results['metadatas'] else {}
                context_chunks.append(f"Document ({meta.get('file_name', 'Unknown')}):\n{doc}")
                
                citations.append(Citation(
                    document_id=meta.get('document_id', ''),
                    file_name=meta.get('file_name', 'Unknown'),
                    snippet=doc[:200] + "..." if len(doc) > 200 else doc
                ))

        context = "\n\n---\n\n".join(context_chunks)
        
        if context:
            prompt = f"""
            You are the Sri Naga Sai ERP AI Assistant. Answer the user's question based strictly on the provided context from company documents.
            If the answer cannot be found in the context, say "I could not find the answer to this in the uploaded documents."
            Do not use outside knowledge.
            If multiple documents are relevant, summarize across them.
            
            Context:
            {context}
            
            User Question: {standalone_query}
            """
        else:
            prompt = f"""
            You are the Sri Naga Sai ERP AI Assistant. The user asked a question, but no relevant company documents were found in the system to answer it.
            Politely inform the user that you don't have any uploaded documents matching their query, but you can help if they upload relevant files.
            
            User Question: {standalone_query}
            """
            
        answer = llm.invoke(prompt).strip()
        
        # Save AI response
        ai_msg = AIChatMessage(
            id=uuid.uuid4(),
            session_id=uuid.UUID(session_id),
            role="ai",
            message=answer
        )
        db.add(ai_msg)
        await db.commit()
        
        return ChatResponse(
            session_id=session_id,
            answer=answer,
            citations=citations
        )
        
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the chat query.")
