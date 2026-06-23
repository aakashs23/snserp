from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class Citation(BaseModel):
    document_id: str
    file_name: str
    snippet: str

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation]

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
