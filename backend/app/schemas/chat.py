from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    message: str

class Citation(BaseModel):
    document_id: str
    file_name: str
    snippet: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
