import uuid
import json
import logging
import fitz  # PyMuPDF
from datetime import datetime
from uuid import UUID

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
import chromadb

from app.config.settings import settings
from app.database.session import async_session_factory
from sqlalchemy import select
from app.models.documents import Document, DocumentMetadata, DocumentAI

logger = logging.getLogger(__name__)

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
collection = chroma_client.get_or_create_collection(name="snserp_documents")

# Initialize Ollama LLM and Embeddings
llm = Ollama(
    base_url=settings.ollama_base_url,
    model=settings.llm_model,
    temperature=0.0
)

embeddings = OllamaEmbeddings(
    base_url=settings.ollama_base_url,
    model=settings.embedding_model
)

import tempfile
import os

# Lazy load OCR to prevent memory bloat on startup if unused
_ocr_instance = None

def get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(use_textline_orientation=True, lang='en', show_log=False)
    return _ocr_instance

async def process_document_background(document_id: UUID, file_bytes: bytes, file_name: str, mime_type: str):
    """
    Background task to process a document:
    1. Extract text
    2. Extract metadata using LLM
    3. Generate embeddings and store in ChromaDB
    4. Update DB models
    """
    try:
        logger.info(f"Starting AI pipeline for document {document_id}")
        
        # 1. Extract text
        extracted_text = ""
        is_pdf = mime_type == "application/pdf"
        is_image = mime_type and mime_type.startswith("image/")
        
        if is_pdf:
            try:
                # Use PyMuPDF to extract text from PDF in memory
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    extracted_text += page.get_text()
                doc.close()
            except Exception as e:
                logger.error(f"PyMuPDF extraction failed: {e}")
        elif mime_type and mime_type.startswith("text/"):
            # Fallback for plain text
            extracted_text = file_bytes.decode('utf-8', errors='ignore')

        # If it's an image, or a PDF with very little selectable text (like a scanned PDF), use PaddleOCR
        if is_image or (is_pdf and len(extracted_text.strip()) < 50):
            logger.info(f"Using PaddleOCR for document {document_id}")
            try:
                ocr = get_ocr()
                
                # PaddleOCR requires a file path for multi-page PDFs or robust image reading
                suffix = ".pdf" if is_pdf else (".jpg" if "jpeg" in mime_type else ".png")
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name
                
                result = ocr.ocr(tmp_path, cls=True)
                
                ocr_text = []
                if result:
                    for idx in range(len(result)):
                        res = result[idx]
                        if res:
                            for line in res:
                                ocr_text.append(line[1][0])
                
                paddle_text = "\n".join(ocr_text)
                
                # For PDFs, combine PyMuPDF text and OCR text if needed, or just use OCR if it's much longer
                if is_pdf and len(extracted_text.strip()) > 0:
                    extracted_text += "\n" + paddle_text
                else:
                    extracted_text = paddle_text
                    
                os.remove(tmp_path)
            except Exception as e:
                logger.error(f"PaddleOCR extraction failed: {e}")

        if not extracted_text.strip():
            logger.warning(f"No text extracted for document {document_id}")
            extracted_text = "No text could be extracted."

        # 2. Extract metadata using LLM
        prompt = f"""
        Analyze the following document text and extract metadata as a strict JSON object.
        Do not output any markdown formatting, only the JSON.
        
        Required fields:
        - title (string): A short, descriptive title.
        - description (string): A 1-2 sentence summary.
        - keywords (list of strings): 3-5 relevant keywords.
        - ai_category (string): Choose ONE from: Invoice, Purchase Order, Agreement, Customer Document, Bank Statement, Government Letter, Receipt, Miscellaneous.
        
        Document Text:
        {extracted_text[:4000]}  # Limit text to avoid context window issues
        """
        
        metadata_json_str = llm.invoke(prompt)
        metadata = {}
        try:
            # Strip markdown code blocks if the LLM adds them
            cleaned_json = metadata_json_str.strip()
            if cleaned_json.startswith("```json"):
                cleaned_json = cleaned_json[7:-3].strip()
            elif cleaned_json.startswith("```"):
                cleaned_json = cleaned_json[3:-3].strip()
            
            metadata = json.loads(cleaned_json)
        except Exception as e:
            logger.error(f"Failed to parse LLM JSON for document {document_id}: {e}\nOutput: {metadata_json_str}")
            metadata = {
                "title": file_name,
                "description": "Metadata extraction failed.",
                "keywords": [],
                "ai_category": "Miscellaneous"
            }

        # 3. Generate Embeddings & Store in ChromaDB
        # We chunk the text roughly to avoid embedding limits
        chunk_size = 1000
        chunks = [extracted_text[i:i+chunk_size] for i in range(0, len(extracted_text), chunk_size)]
        
        if chunks:
            collection.add(
                documents=chunks,
                metadatas=[{"document_id": str(document_id), "file_name": file_name} for _ in chunks],
                ids=[f"{str(document_id)}_chunk_{i}" for i in range(len(chunks))]
            )

        # 4. Update Database
        async with async_session_factory() as session:
            # Update Document AI Category
            doc = await session.get(Document, document_id)
            if doc:
                doc.ai_category = metadata.get("ai_category", "Miscellaneous")
            
            # Insert Metadata
            doc_meta = DocumentMetadata(
                id=uuid.uuid4(),
                document_id=document_id,
                title=metadata.get("title", file_name),
                description=metadata.get("description", ""),
                keywords=metadata.get("keywords", [])
            )
            session.add(doc_meta)
            
            # Update DocumentAI state
            result = await session.execute(select(DocumentAI).where(DocumentAI.document_id == document_id))
            doc_ai = result.scalar_one_or_none()
            if doc_ai:
                doc_ai.ocr_text = extracted_text
                doc_ai.summary = metadata.get("description", "")
                doc_ai.embedding_status = "completed"
                doc_ai.processed_at = datetime.utcnow()
            else:
                doc_ai = DocumentAI(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    ocr_text=extracted_text,
                    summary=metadata.get("description", ""),
                    embedding_status="completed",
                    processed_at=datetime.utcnow()
                )
                session.add(doc_ai)
                
            await session.commit()
            logger.info(f"Successfully processed document {document_id}")

    except Exception as e:
        logger.error(f"Error in background AI pipeline for document {document_id}: {e}")
        async with async_session_factory() as session:
            result = await session.execute(select(DocumentAI).where(DocumentAI.document_id == document_id))
            doc_ai = result.scalar_one_or_none()
            if doc_ai:
                doc_ai.embedding_status = "failed"
                await session.commit()
