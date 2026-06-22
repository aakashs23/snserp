import re

from fastapi import APIRouter, Depends, HTTPException
import chromadb
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.schemas.chat import ChatRequest, ChatResponse, Citation
from app.models.users import User
from app.models.documents import Document, DocumentAI, DocumentMetadata
from app.middleware.auth import get_current_user
from app.database.session import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

FILENAME_PATTERN = re.compile(
    r"([A-Za-z0-9][A-Za-z0-9 _().-]*\.(?:pdf|doc|docx|txt|png|jpg|jpeg))",
    re.IGNORECASE,
)
QUERY_TERM_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{2,}")
STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "what", "when",
    "where", "which", "about", "into", "your", "have", "has", "had", "are",
    "was", "were", "will", "would", "could", "should", "please", "show",
    "tell", "find", "give", "there", "their", "them", "they", "document",
    "documents", "file", "files", "pdf",
}

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
collection = chroma_client.get_or_create_collection(name="snserp_documents")

# Initialize Ollama LLM and Embeddings
llm = Ollama(
    base_url=settings.ollama_base_url,
    model=settings.llm_model,
    temperature=0.2
)

embeddings = OllamaEmbeddings(
    base_url=settings.ollama_base_url,
    model=settings.embedding_model
)


def _extract_query_terms(message: str) -> list[str]:
    terms = []
    seen = set()
    for raw_term in QUERY_TERM_PATTERN.findall(message.lower()):
        if raw_term in STOPWORDS or raw_term in seen:
            continue
        seen.add(raw_term)
        terms.append(raw_term)
    return terms[:8]


async def _find_matching_documents(
    db: AsyncSession,
    current_user_id,
    filenames: list[str],
) -> list[tuple[Document, DocumentAI]]:
    if not filenames:
        return []

    filename_filters = []
    for filename in filenames:
        filename_filters.append(Document.original_name.ilike(f"%{filename}%"))
        filename_filters.append(Document.file_name.ilike(f"%{filename}%"))

    result = await db.execute(
        select(Document, DocumentAI)
        .outerjoin(DocumentAI, DocumentAI.document_id == Document.id)
        .where(
            Document.uploaded_by == current_user_id,
            Document.is_deleted == False,
            or_(*filename_filters),
        )
        .order_by(Document.upload_date.desc())
    )
    return result.all()


async def _search_documents_by_keywords(
    db: AsyncSession,
    current_user_id,
    query_terms: list[str],
) -> list[tuple[Document, DocumentAI, DocumentMetadata | None]]:
    if not query_terms:
        return []

    keyword_filters = []
    for term in query_terms:
        pattern = f"%{term}%"
        keyword_filters.extend(
            [
                Document.original_name.ilike(pattern),
                Document.ai_category.ilike(pattern),
                DocumentAI.summary.ilike(pattern),
                DocumentAI.ocr_text.ilike(pattern),
                DocumentMetadata.title.ilike(pattern),
                DocumentMetadata.description.ilike(pattern),
            ]
        )

    result = await db.execute(
        select(Document, DocumentAI, DocumentMetadata)
        .join(DocumentAI, DocumentAI.document_id == Document.id)
        .outerjoin(DocumentMetadata, DocumentMetadata.document_id == Document.id)
        .where(
            Document.uploaded_by == current_user_id,
            Document.is_deleted == False,
            DocumentAI.embedding_status == "completed",
            or_(*keyword_filters),
        )
        .order_by(Document.upload_date.desc())
        .limit(3)
    )
    return result.all()

@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        explicit_filenames = [match.strip() for match in FILENAME_PATTERN.findall(request.message)]
        query_terms = _extract_query_terms(request.message)
        matched_documents = await _find_matching_documents(
            db=db,
            current_user_id=current_user.id,
            filenames=explicit_filenames,
        )

        # 1. Embed the query
        query_embedding = embeddings.embed_query(request.message)

        # 2. Search ChromaDB
        search_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": 5,
            "include": ["documents", "metadatas"],
        }

        if matched_documents:
            matched_ids = [str(document.id) for document, _ in matched_documents]
            if len(matched_ids) == 1:
                search_kwargs["where"] = {"document_id": matched_ids[0]}

        results = collection.query(**search_kwargs)

        citations = []
        context_chunks = []

        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i] if results['metadatas'] else {}
                context_chunks.append(f"Source Document ({meta.get('file_name', 'Unknown')}):\n{doc}")

                citations.append(Citation(
                    document_id=meta.get('document_id', ''),
                    file_name=meta.get('file_name', 'Unknown'),
                    snippet=doc[:200] + "..." if len(doc) > 200 else doc
                ))

        # If the user named a specific completed document and vector retrieval returned
        # nothing usable, fall back to stored OCR text so "Indexed" documents remain
        # answerable even when the vector store path or document-name matching drifts.
        if not context_chunks and matched_documents:
            for document, document_ai in matched_documents[:3]:
                if not document_ai or document_ai.embedding_status != "completed":
                    continue
                if not document_ai.ocr_text:
                    continue

                snippet = document_ai.ocr_text[:4000]
                context_chunks.append(
                    f"Source Document ({document.original_name}):\n{snippet}"
                )
                citations.append(
                    Citation(
                        document_id=str(document.id),
                        file_name=document.original_name,
                        snippet=snippet[:200] + "..." if len(snippet) > 200 else snippet,
                    )
                )

        # General fallback for ordinary prompts: search completed OCR/metadata
        # text in Postgres when vector retrieval misses.
        if not context_chunks:
            keyword_matches = await _search_documents_by_keywords(
                db=db,
                current_user_id=current_user.id,
                query_terms=query_terms,
            )
            for document, document_ai, document_metadata in keyword_matches:
                snippet_source = (
                    document_ai.ocr_text
                    or document_ai.summary
                    or (document_metadata.description if document_metadata else "")
                )
                if not snippet_source:
                    continue

                snippet = snippet_source[:4000]
                context_chunks.append(
                    f"Source Document ({document.original_name}):\n{snippet}"
                )
                citations.append(
                    Citation(
                        document_id=str(document.id),
                        file_name=document.original_name,
                        snippet=snippet[:200] + "..." if len(snippet) > 200 else snippet,
                    )
                )

        # 3. If no context found, answer directly but state no documents were found
        context = "\n\n---\n\n".join(context_chunks)

        if context:
            prompt = f"""
            You are the Sri Naga Sai ERP AI Assistant. Answer the user's question based strictly on the provided context from company documents.
            If the answer cannot be found in the context, say "I could not find the answer to this in the uploaded documents."
            Do not use outside knowledge.
            
            Context:
            {context}
            
            User Question: {request.message}
            """
        else:
            requested_doc_text = (
                f" related to {', '.join(explicit_filenames)}"
                if explicit_filenames
                else ""
            )
            prompt = f"""
            You are the Sri Naga Sai ERP AI Assistant. The user asked a question, but no relevant company documents were found in the system to answer it.
            Politely inform the user that you don't have any uploaded documents matching their query, but you can help if they upload relevant files.

            No matching indexed content was found{requested_doc_text}.

            User Question: {request.message}
            """
            
        answer = llm.invoke(prompt)
        
        return ChatResponse(
            answer=answer.strip(),
            citations=citations
        )
        
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the chat query.")
