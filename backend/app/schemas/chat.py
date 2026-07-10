from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class ChatRequest(BaseModel):
    # Capped before the message is interpolated into an LLM prompt. 4000 matches
    # the truncation width chat.py already applies to retrieved OCR context.
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None

class Citation(BaseModel):
    document_id: str
    file_name: str
    snippet: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    relevance_score: Optional[float] = None

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation]
    confidence: Optional[float] = None
    provider: Optional[str] = None

class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role: str
    message: str
    created_at: datetime
    # We could parse citations from the message if we store it as JSON, 
    # but for simplicity, the frontend can just render the markdown.

class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: Optional[str] = None
    created_at: datetime
