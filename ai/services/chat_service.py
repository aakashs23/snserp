"""AI Chat service using Qwen 3 via Ollama for document-aware conversations."""


class ChatService:
    """RAG-powered chat service for answering questions from company documents."""

    def __init__(self):
        pass

    async def initialize(self):
        """Initialize LLM connection via Ollama."""
        # TODO: Set up Ollama client for Qwen 3
        pass

    async def chat(self, user_message: str, session_id: str | None = None) -> dict:
        """Process a user message and generate an AI response with document context."""
        # TODO: Implement RAG chat flow
        raise NotImplementedError

    async def summarize_document(self, document_text: str) -> str:
        """Generate a summary of a document."""
        # TODO: Implement document summarization
        raise NotImplementedError
